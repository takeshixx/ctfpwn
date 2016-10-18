import time


class Flag:
    """A class that represents flags, as parsed from incoming lines. See REGEX_INPUT
    and the corresponding input format example."""

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