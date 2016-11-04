import time
import yaml
import os.path


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


def load_ctf_config(path):
    if not path or not os.path.isfile(path):
        path = os.path.join(os.path.dirname(__file__), '../config.yaml')
    path = open(path, 'r')
    try:
        conf = yaml.load(path.read())
    except yaml.YAMLError as e:
        print(e)
        return
    return conf
