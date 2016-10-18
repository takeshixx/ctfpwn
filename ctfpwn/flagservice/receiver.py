"""This module is responsible for listening on a TCP port to receive flags
that will be inserted into the database.

This may be obsolete because the exploit supervisor pushes flags directly
to the database. However, it could still run for testing purposes during
exploit development."""
import re
import asyncio
import logging
import codecs

from helperlib.logging import scope_logger

from ctfpwn import Flag

log = logging.getLogger(__name__)

# TODO: move to config file
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

VALIDATE = re.compile(REGEX_INPUT)


@scope_logger
class FlagReceiverProtocol(asyncio.Protocol):
    def __init__(self, db):
        super(FlagReceiverProtocol, self).__init__()
        self.db = db

    def connection_made(self, transport):
        self.transport = transport
        self.peername = transport.get_extra_info('peername')

    def data_received(self, data):
        for line in data.split(b'\n'):
            if not VALIDATE.findall(line):
                self._writeline('Bogus format!')
                log.debug('Erroneous flag submission by: ' + self.peername)
                continue
            flag = Flag(*line.strip().split(b'|'))
            self.db.insert_new(flag)
            self._writeline('Accepted')

    def _writeline(self, data):
        if isinstance(data, str):
            data = codecs.encode(data)
        self.transport.write(data + b'\n')
