import time


class Flag():
    """A class that represents flags, as parsed from incoming lines. See REGEX_INPUT
    and the corresponding input format example."""
    def __init__(self, incoming):
        self.service = incoming[0]
        self.target = incoming[1]
        self.flag = incoming[2]
        self.timestamp = int(time.time())


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