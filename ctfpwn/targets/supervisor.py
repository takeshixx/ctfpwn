import asyncio
import functools
import time
import ipaddress

from libnmap.parser import NmapParser, NmapParserException
from helperlib.logging import scope_logger

from ctfpwn.targets.worker import TargetWorkerProtocol


@scope_logger
class TargetSupervisor(object):
    """The supervisor manages all running exploit instances."""
    def __init__(self, db, loop=None, networks=None, discover_ports=None,
                 service_ports=None, *args, **kwargs):
        self.db = db
        self.loop = loop or asyncio.get_event_loop()
        self.sem = asyncio.Semaphore(100)
        self.target_networks = self._populate_networks(networks)
        self.discover_ports = discover_ports or [22, 80, 8080]
        self.service_ports = service_ports or [80, 9090]

    def __repr__(self):
        return object.__repr__(self)

    def _populate_networks(self, networks):
        """This function returns a Nmap-compliant list of
        all network ranges as str. The input should be any
        of the following representations:

        192.168.0.1
        192.168.1-5.3
        192.168.0.0/24

        If there are multiple subnetworks, they should be
        seperated by commas, e.g.:

        192.168.1-5.3,192.168.0.0/24,192.168.0.1"""
        assert isinstance(networks, (str, bytes)), 'Invalid networks type'
        if isinstance(networks, bytes):
            networks = networks.decode()
        networks = networks.split(',')
        targets = set()
        for network in networks:
            try:
                _targets = ipaddress.ip_network(network, strict=False)
            except ValueError:
                self.log.debug('Invalid network definition: %s', network)
                continue
            if '/' in network:
                _targets = _targets.hosts()
            for _target in _targets:
                targets.add(str(_target))
        out = ''
        for i, target in enumerate(list(targets)):
            out += target
            if i != (len(targets) - 1):
                out += ' '
        return out

    def start(self, discovery_interval, service_interval):
        """The main supervisor starting point that schedules
        both the target discovery and service checker long
        running tasks."""
        async def _run_discovery(interval):
            while True:
                await self.discover_targets()
                await asyncio.sleep(interval)
        self.loop.create_task(_run_discovery(discovery_interval))
        async def _run_service_checks(interval):
            while True:
                await self.check_services()
                await asyncio.sleep(interval)
        self.loop.create_task(_run_service_checks(service_interval))

    async def discover_targets(self):
        """Discovers alive targets in the CTF network range."""
        self.log.info('Running Target Discovery')
        future = self.loop.create_future()
        cmd = ['nmap', '-T5', '-sn', '-v', '-oX', '-', '-PS',
               ','.join([str(x) for x in self.discover_ports]), self.target_networks]
        transport, protocol = await self.loop.subprocess_exec(
            lambda: TargetWorkerProtocol(future),
            *cmd,
            stdin=None)
        process_started = int(time.time())
        future.add_done_callback(functools.partial(
            self.discover_callback,
            future,
            protocol,
            transport,
            process_started))
        return future

    def discover_callback(self, future, protocol, transport, process_started, *args, **kwargs):
        """Update discovery results in database. This is
        the callback for discover_targets() which mainly
        inserts the scanning results into the database."""
        process_finished = int(time.time())
        output = bytes(protocol.output)
        try:
            parser = NmapParser.parse(output.decode())
        except NmapParserException as e:
            self.log.exception(e)
            return
        self.log.info('Scanned %d targets: ', parser.hosts_total)
        self.log.info('Found %d alive targets', parser.hosts_up)
        for host in parser.hosts:
            self.loop.create_task(self.db.update_target(host.address, host.is_up()))

    async def check_services(self):
        """Identify running services on alive targets."""
        targets = await self.db.select_alive_targets()
        if not targets:
            self.log.info('No alive targets found, skipping service checks')
            return
        self.log.info('Checking %d services on %d targets', len(self.service_ports), len(targets))
        for target in targets:
            self.loop.create_task(self.check_target(target.get('host')))

    async def check_target(self, target):
        """Check a single target IP for running services."""
        self.log.info('Checking Target %s', target)
        future = self.loop.create_future()
        if not self.service_ports:
            return
        elif len(self.service_ports) == 1:
            ports = str(self.service_ports[0])
        else:
            ports = ','.join([str(x) for x in self.service_ports])
        cmd = ['nmap', '-T5', '-v', '-oX', '-','-p', ports, target]
        transport, protocol = await self.loop.subprocess_exec(
            lambda: TargetWorkerProtocol(future),
            *cmd,
            stdin=None)
        process_started = int(time.time())
        future.add_done_callback(functools.partial(
            self.target_callback,
            future,
            protocol,
            transport,
            process_started))
        return future

    def target_callback(self, future, protocol, transport, process_started, *args, **kwargs):
        """Update service checking results in database.
        This is the callback for check_target()
        which mainly inserts the scanning results into
        the database."""
        process_finished = int(time.time())
        output = bytes(protocol.output)
        try:
            parser = NmapParser.parse(output.decode())
        except NmapParserException as e:
            self.log.exception(e)
            return
        try:
            host = parser.hosts[0]
            ports = [x[0] for x in host.get_open_ports()]
        except IndexError:
            return
        if not ports:
            return
        self.log.info('Found %d running service(s) on target %s', len(ports), host.address)
        self.loop.create_task(self.db.update_target_services(host.address, ports))
