"""This module is responsible for listening on a TCP port to receive flags
that will be inserted into the database.

This may be obsolete because the exploit supervisor pushes flags directly
to the database. However, it could still run for testing purposes during
exploit development."""
import re
from twisted.internet import protocol
from helperlib.logging import scope_logger

from .shared import flag_db
from flagservice.flag import Flag

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
).encode()

input_validation = re.compile(REGEX_INPUT)


@scope_logger
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
            lines = incoming.split(b'\n')
            for line in lines:
                if not line:
                    continue
                line = line.strip()
                if input_validation.findall(line):
                    flagdata = line.strip().decode('utf-8', errors='replace').split('|')
                    flag = Flag(flagdata[0], flagdata[1], flagdata[2])
                    flag_db.insert_new(flag)
                    self.transport.write(b'received\n')
                else:
                    self.transport.write(b'bogus format!\n')
                    self.log.debug('False submission by %s', self.transport.getPeer())
        except Exception as e:
            self.log.warning('Error in dataReceive() function! [EXCEPTION: %s]', e)
