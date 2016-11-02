"""This module includes everything that is needed to submit flags to
the gameserver."""
import time
import asyncio
import logging
import codecs

from helperlib.logging import scope_logger

log = logging.getLogger(__name__)
LOG_LEVEL_STAT = logging.INFO + 1
logging.addLevelName(LOG_LEVEL_STAT, 'STATISTIC')

# TODO: move to config file
# Gameserver settings
GAMESERVER_ADDR = '127.0.0.1'
GAMESERVER_PORT = 9000
# How many flags should be submitted at the same time at max.
MAX_FLAG_SUBMITS = 1000
# Messages by the gameserver, need to be adjusted
GAME_SERVER_MSG_SUCCESS = b'accepted'
GAME_SERVER_MSG_SUCCESS2 = b'congratulations'
GAME_SERVER_MSG_EXPIRED = b'expired'
GAME_SERVER_MSG_SERVICE_DOWN = b'corresponding'
GAME_SERVER_MSG_INVALID = b'no such flag'
GAME_SERVER_MSG_OWN_FLAG = b'own flag'
GAME_SERVER_MSG_TOO_MUCH = b'too much'
GAME_SERVER_MSG_ALREADY_SUBMITTED = b'already submitted'


async def submitter(db, loop):
    """Flag submission job, runs every SERVICE_SUBMIT_INTERVAL
    seconds."""
    log.debug('Called subbmiter')
    t0 = time.time()
    flags = await db.select_new_and_pending_flags(limit=MAX_FLAG_SUBMITS)
    if flags:
        log.info('[SUBMIT] [COUNT %d]', len(flags))
        loop.create_connection(lambda: FlagSubmissionProtocol(flags, db),
                               GAMESERVER_ADDR,
                               GAMESERVER_PORT)
    else:
        log.info('[SUBMIT] No NEW/PENDING flags for submission...')
    log.debug('Finished submitter(), took %f', time.time() - t0)


@scope_logger
class FlagSubmissionProtocol(asyncio.Protocol):
    """An interface to the gameserver for submitting flags.
    Every instance may submit one or more flags at once."""
    def __init__(self, flags, flag_db, timeout=5):
        self.flags = flags
        self.db = flag_db
        self.current_flag = None
        self.flags_success = list()
        self.flags_failed = list()
        self.flags_expired = list()
        self.flags_pending = list()
        self.connection_timeout = timeout

    def timeout(self):
        """This function will be called if a timeout occurs."""
        self.transport.close()

    def connection_made(self, transport):
        self.transport = transport
        self.log.debug('[GAMESERVER] [CONNECTED]')
        # Start 5 seconds timeout timer
        self.h_timeout = asyncio.get_event_loop().call_later(
            self.connection_timeout, self.timeout)

    def data_received(self, incoming):
        if GAME_SERVER_MSG_SUCCESS in incoming or GAME_SERVER_MSG_SUCCESS2 in incoming:
            self.flags_success.append(self.current_flag.get('flag'))
        elif GAME_SERVER_MSG_SERVICE_DOWN in incoming:
            self.log.error('[%s] [GAMESERVER REPORTED SERVICE NOT AVAILABLE]',
                self.current_flag.get('service'))
            self.flags_pending.append(self.current_flag.get('flag'))
        elif GAME_SERVER_MSG_EXPIRED in incoming:
            # log.debug('Flag expired')
            self.flags_expired.append(self.current_flag.get('flag'))
        elif GAME_SERVER_MSG_INVALID in incoming:
            # log.debug('Invalid flag')
            self.flags_failed.append(self.current_flag.get('flag'))
        elif GAME_SERVER_MSG_OWN_FLAG in incoming:
            # log.debug('Own flag')
            self.flags_failed.append(self.current_flag.get('flag'))
        elif GAME_SERVER_MSG_ALREADY_SUBMITTED in incoming:
            # log.debug('Flag already submitted')
            self.flags_failed.append(self.current_flag.get('flag'))
        elif GAME_SERVER_MSG_TOO_MUCH in incoming:
            """TODO: The gameserver may complains about too much connections from our team.
            This message has to be adjusted. Abort the current session and retry the current
            flags in the next iteration."""
            self.log.warning('Too much connections to the gameserver!')
            self.transport.close()
            return
        else:
            self.log.warning('Unknown gameserver message: %r', incoming.strip())

        if not len(self.flags):
            self.transport.close()
            return

        # Restart timeout timer
        self.h_timeout.cancel()
        self.h_timeout = asyncio.get_event_loop().call_later(
            self.connection_timeout, self.timeout)

        self.current_flag = self.flags.pop(0)
        self._writeline(self.current_flag.get('flag'))

    def connection_lost(self, reason):
        log.debug('Lost Game Server connection')
        self.h_timeout.cancel()
        self._update_flag_states()

    def _writeline(self, data):
        if isinstance(data, str):
            data = codecs.encode(data)
        self.transport.write(data + b'\n')

    def _update_flag_states(self):
        t0 = time.time()

        if self.flags_success:
            for flag in self.flags_success:
                self.db.update_submitted(flag)

        if self.flags_pending:
            for flag in self.flags_pending:
                self.db.update_pending(flag)

        if self.flags_expired:
            for flag in self.flags_expired:
                self.db.update_expired(flag)

        if self.flags_failed:
            for flag in self.flags_failed:
                self.db.update_failed(flag)

        # If the connection has been lost prematurely,
        # mark the not yet processed flags as PENDING.
        if self.flags:
            for flag in self.flags:
                self.db.update_pending(flag)

        self.log.log(LOG_LEVEL_STAT, '[SUBMIT] [ACCEPTED %d] [PENDING %d] [EXPIRED %d] [UNKNOWN %d]',
            len(self.flags_success),
            len(self.flags_pending + self.flags),
            len(self.flags_expired),
            len(self.flags_failed))
        self.log.log(LOG_LEVEL_STAT, '[GAMESERVER] _update_flag_states() took %f', time.time() - t0)
