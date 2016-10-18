class Target():
    """
    An instance represents a single target system. It should provide
    information if the host is alive (pingable) and which service
    ports are open.
    """
    def __init__(self, host):
        self.host = host
        self.is_alive = False
        self.services_alive = []