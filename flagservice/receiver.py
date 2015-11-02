"""This module is responsible for listening on a TCP port to receive flags
that will be inserted into the database."""
import re
from twisted.python import log
from twisted.internet import protocol

from .shared import flag_db
from .flagdb import Flag

# Flag regex
# Input format example: 'smartgrid|10.23.103.2|JAJAJAJAJAJAJAJAJAJAJAJAJAJAJAA=|1446295211'
REGEX_FLAG = r"(\w{31}=)"
REGEX_SERVICE = r"(\w+)"
REGEX_IP = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
REGEX_TIMESTAMP = r"(\d{10})"
REGEX_INPUT = '^{}\|{}\|{}\|{}$'.format(
    REGEX_SERVICE,
    REGEX_IP,
    REGEX_FLAG,
    REGEX_TIMESTAMP
)

input_validation = re.compile(REGEX_INPUT)

class FlagReceiverProtocol(protocol.Protocol):
    """
    Protocol factory for flag submission.
    """
    def dataReceived(self, incoming):
        """
        Instance function that actually handles incoming data. If lines math
        REGEX_INPUT, it will be inserted into the database.
        """
        try:
            lines = incoming.split('\n')
            for line in lines:
                if not line:
                    continue
                line = line.strip()
                if input_validation.findall(line):
                    flag = Flag(line.strip().split('|'))
                    flag_db.insert_new(flag)
                else:
                    self.transport.write('bogus format!\n')
        except Exception as e:
            log.msg('Error in dataReceive() function! [EXCEPTION: {}]'.format(e))