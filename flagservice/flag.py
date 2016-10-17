import time


class Flag():
    """A class that represents flags, as parsed from incoming lines. See REGEX_INPUT
    and the corresponding input format example."""
    def __init__(self, incoming):
        self.service = incoming[0]
        self.target = incoming[1]
        self.flag = incoming[2]
        self.timestamp = int(time.time())