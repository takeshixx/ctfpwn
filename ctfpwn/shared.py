# encoding: utf8
import time
import pathlib
import logging
from helperlib.logging import default_config

from .config import ReloadableConfig

log = logging.getLogger(__name__)


class Flag(object):
    """A class that represents flags, as parsed
    from incoming lines. See REGEX_INPUT and the
    corresponding input format example."""
    def __init__(self, service, target, flag):
        self.service = service
        self.target = target
        self.flag = flag
        self.timestamp = int(time.time())


class Target(object):
    """An instance represents a single target system.
    t should provide information if the host is
    alive (pingable) and which service ports are open."""
    def __init__(self, host):
        self.host = host
        self.is_alive = False
        self.services_alive = list()
        self.services_fixed = list()


class Service(object):
    """This class should be used whenever a service
    is working on vulnerable services that will be
    processed."""
    def __init__(self, name, service_type, port=0,
                 url='', meta=''):
        self.name = name
        self.type = service_type
        self.port = port
        self.url = url
        self.meta = meta


def load_ctf_config(path, logging_section=None):
    if path and not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    if not path or not path.is_file():
        path = pathlib.Path(__file__).parent.parent / 'config.yaml'

    if not logging_section:
        default_config(level=logging.DEBUG, disable_existing_loggers=False)
        logging_section = 'default'

    return ReloadableConfig(path, logging_section)


class TooMuchConnectionsException(Exception):
    pass
