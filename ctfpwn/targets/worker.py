import asyncio
import subprocess

from helperlib.logging import scope_logger


@scope_logger
class TargetWorkerProtocol(asyncio.SubprocessProtocol):
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
