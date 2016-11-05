import asyncio
import subprocess
import time
import functools

from libnmap.parser import NmapParser, NmapParserException

from helperlib.logging import scope_logger


@scope_logger
class TransportWorker(object):
    def __init__(self, db, loop=None):
        self.db = db
        self.loop = loop or asyncio.get_event_loop()
        self.target = None
        self.services = None

    async def check_target_ports(self, target, services):
        """Check a single target IP for running services."""
        self.log.debug('Checking %d service port(s) on target %s',
                       len(services),
                       target.get('host'))
        self.target = target
        self.services = services
        future = self.loop.create_future()
        ports = list()
        for service in self.services:
            ports.append(service.get('port'))
        if not ports:
            return
        elif len(ports) == 1:
            ports = str(ports[0])
        else:
            ports = ','.join([str(x) for x in ports])
        cmd = ['nmap', '-T5', '-v', '-oX', '-','-p', ports, target.get('host')]
        transport, protocol = await self.loop.subprocess_exec(
            lambda: TransportWorkerProtocol(future),
            *cmd,
            stdin=None)
        process_started = int(time.time())
        future.add_done_callback(functools.partial(
            self.check_target_ports_callback,
            future,
            protocol,
            transport,
            process_started))
        return future

    def check_target_ports_callback(self, future, protocol, transport, process_started, *args, **kwargs):
        """Update service checking results in database.
        This is the callback for check_target() which
        mainly inserts the scanning results into the
        database."""
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
        alive_services = list()
        for port in ports:
            for service in self.services:
                if service.get('port') == port:
                    alive_services.append(service.get('id'))
        self.log.info('Found %d running service(s) on target %s', len(ports), host.address)
        self.loop.create_task(self.db.update_target_services(host.address, alive_services))


@scope_logger
class TransportWorkerProtocol(asyncio.SubprocessProtocol):
    """An instance of this protocol represents a running
    Nmap process."""
    def __init__(self, future, cmd=None):
        self.future = future
        self.output = bytearray()
        self.cmd = cmd

    def connection_made(self, transport):
        self.transport = transport
        self.pid = transport.get_pid()

    def stop(self):
        self.log.debug('stopping %d', self.pid)
        if self.transport.get_pid():
            self.transport.terminate()
            loop = asyncio.get_event_loop()
            loop.call_later(5, self.kill)

    def kill(self):
        self.log.debug('killing %d', self.pid)
        if self.transport.get_pid():
            self.transport.kill()

    def pipe_data_received(self, fd, data):
        self.output.extend(data)

    def process_exited(self):
        return_code = self.transport.get_returncode()
        if return_code is 0:
            self.future.set_result(self.output)
        else:
            self.future.set_exception(subprocess.CalledProcessError(return_code, self.cmd))
