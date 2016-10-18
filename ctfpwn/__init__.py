import time

from .exploitservice import run_exploitservice
from .flagservice import run_flagservice


class Flag:
    """A class that represents flags, as parsed
    from incoming lines. See REGEX_INPUT and the
    corresponding input format example."""
    def __init__(self, service, target, flag):
        """
        :type service: str
        :type target: str
        :type flag: str
        """
        self.service = service
        self.target = target
        self.flag = flag
        self.timestamp = int(time.time())


class Target():
    """An instance represents a single target system.
    t should provide information if the host is
    alive (pingable) and which service ports are open."""
    def __init__(self, host):
        self.host = host
        self.is_alive = False
        self.services_alive = []