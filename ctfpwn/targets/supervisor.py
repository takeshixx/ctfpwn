import asyncio
import functools
import time
import ipaddress
import subprocess

from libnmap.parser import NmapParser, NmapParserException
from helperlib.logging import scope_logger

from ctfpwn.targets.workers.transport import TransportWorker, TransportWorkerProtocol
from ctfpwn.targets.workers.application import HttpWorker


@scope_logger
class TargetSupervisor(object):
    """The supervisor manages all running exploit instances."""
    def __init__(self, db, config, loop=None, networks=None, discover_ports=None,
                 *args, **kwargs):
        self.db = db
        self.config = config
        self.loop = loop or asyncio.get_event_loop()
        self.sem = asyncio.Semaphore(100)
        self.target_networks = self._populate_networks(config.get('ctf_network'))
        self.exclude_targets = self._populate_networks(config.get('ctf_network_exclude'))
        self.discover_ports = config.get('discovery_ports')

    def __repr__(self):
        return object.__repr__(self)

    def _populate_networks(self, networks):
        """This function returns a Nmap-compliant list of
        all network ranges as str. The input should be any
        of the following representations:

        192.168.0.1
        192.168.0.0/24

        If there are multiple subnetworks, they should be
        separated by commas, e.g.:

        192.168.0.0/24,192.168.0.1"""
        if not networks:
            return list()
        assert isinstance(networks, (str, bytes)), 'Invalid networks type'
        if isinstance(networks, bytes):
            networks = networks.decode()
        networks = networks.split(',')
        target_networks = set()
        for network in networks:
            # TODO: won't work for network definitions like 10.60.1-255.2
            # try:
            #     _targets = ipaddress.ip_network(network, strict=False)
            # except ValueError:
            #     self.log.debug('Invalid network definition: %s', network)
            #     continue
            target_networks.add(network)
        return list(target_networks)

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

    async def check_services(self):
        """Identify running services on alive targets."""
        targets = await self.db.select_alive_targets()
        if not targets:
            self.log.info('No alive targets found, skipping service checks')
            return
        port_services = await self.db.select_services(service_type='port')
        url_services = await self.db.select_services(service_type='url')
        if not port_services and not url_services:
            self.log.info('No services found, skipping service checks')
            return
        self.log.info('Checking %d services on %d targets', len(port_services) + len(url_services), len(targets))
        for target in targets:
            if target.get('host') in self.exclude_targets:
                continue
            if port_services:
                worker = TransportWorker(self.db)
                self.loop.create_task(worker.check_target_ports(
                    target,
                    services=port_services))
            if url_services:
                worker = HttpWorker(self.db)
                self.loop.create_task(worker.check_target_urls(
                    target,
                    services=url_services))

    async def discover_targets(self):
        """Discovers alive targets in the CTF network range."""
        self.log.info('Running Target Discovery')
        future = self.loop.create_future()
        cmd = ['nmap', '-T5', '-sn', '-v', '-oX', '-', '-PS',
               ','.join([str(x) for x in self.discover_ports]),
               '--exclude', self.exclude_targets,
               *self.target_networks]
        transport, protocol = await self.loop.subprocess_exec(
            lambda: TransportWorkerProtocol(future),
            *cmd,
            stdin=None,
            stderr=subprocess.STDOUT)
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
        if future.exception():
            self.log.exception(future.exception())
        process_finished = int(time.time())
        output = bytes(protocol.output)
        try:
            parser = NmapParser.parse(output.decode())
        except NmapParserException as e:
            self.log.exception(e)
            return
        self.log.info('Scanned %d target(s), %d are alive', parser.hosts_total, parser.hosts_up)
        for host in parser.hosts:
            self.loop.create_task(self.db.update_target(host.address, host.is_up()))
