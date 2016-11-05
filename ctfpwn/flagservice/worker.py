"""This module includes everything that is needed to
submit flags to the game server."""
import time
import asyncio
import logging
import codecs

from helperlib.logging import scope_logger

from ctfpwn.shared import TooMuchConnectionsException

log = logging.getLogger(__name__)
LOG_LEVEL_STAT = logging.INFO + 1
logging.addLevelName(LOG_LEVEL_STAT, 'STATISTIC')


@scope_logger
class FlagSubmissionProtocol(asyncio.Protocol):
    """An interface to the gameserver for submitting flags.
    Every instance may submit one or more flags at once."""
    def __init__(self, flags, flag_db, config, future,
                 loop=None, timeout=5):
        self.flags = flags
        self.db = flag_db
        self.loop = loop or asyncio.get_event_loop()
        self.config = config
        self.future = future
        self.current_flag = None
        self.flags_success = list()
        self.flags_failed = list()
        self.flags_expired = list()
        self.flags_pending = list()
        self.connection_timeout = timeout
        self.ready_for_submission = False

    def timeout(self):
        """This function will be called
        if a timeout occurs."""
        self.transport.close()

    def reset_timer(self):
        # Restart timeout timer
        self.h_timeout.cancel()
        self.h_timeout = asyncio.get_event_loop().call_later(
            self.connection_timeout, self.timeout)

    def connection_made(self, transport):
        self.transport = transport
        self.log.debug('[GAMESERVER] Connection established')
        # Start 5 seconds timeout timer
        self.h_timeout = asyncio.get_event_loop().call_later(
            self.connection_timeout, self.timeout)

    def data_received(self, incoming):
        incoming = incoming.decode().strip()
        if not self.ready_for_submission:
            if not incoming.endswith(self.config.get('game_server_msg_ready')):
                self.log.debug('[GAMESERVER] Gameserver is not ready yet')
                self.reset_timer()
                return
            else:
                self.log.debug('[GAMESERVER] Gameserver is ready, sending flags')
                self.ready_for_submission = True
        else:
            if self.config.get('game_server_msg_success') in incoming or \
                            self.config.get('game_server_msg_success2') in incoming:
                self.flags_success.append(self.current_flag.get('flag'))
            elif self.config.get('game_server_msg_service_down') in incoming:
                self.log.error('[GAMESERVER] [%s] GAMESERVER REPORTED SERVICE NOT AVAILABLE!',
                    self.current_flag.get('service'))
                self.flags_pending.append(self.current_flag.get('flag'))
            elif self.config.get('game_server_msg_expired') in incoming:
                # log.debug('Flag expired')
                self.flags_expired.append(self.current_flag.get('flag'))
            elif self.config.get('game_server_msg_invalid') in incoming:
                # log.debug('Invalid flag')
                self.flags_failed.append(self.current_flag.get('flag'))
            elif self.config.get('game_server_msg_own_flag') in incoming:
                # log.debug('Own flag')
                self.flags_failed.append(self.current_flag.get('flag'))
            elif self.config.get('game_server_msg_already_submitted') in incoming:
                # log.debug('Flag already submitted')
                self.flags_failed.append(self.current_flag.get('flag'))
            elif self.config.get('game_server_msg_too_much') in incoming:
                self.log.warning('[GAMESERVER] Too much connections to the gameserver!')
                self.future.set_exception(TooMuchConnectionsException)
                self.transport.close()
                return
            else:
                self.log.warning('Unknown gameserver message: %r', incoming.strip())

        if not len(self.flags):
            self.transport.close()
            return
        self.reset_timer()
        self.current_flag = self.flags.pop(0)
        self._writeline(self.current_flag.get('flag'))

    def connection_lost(self, reason):
        log.debug('[GAMESERVER] Lost Gameserver connection')
        self.h_timeout.cancel()
        if not self.future.done():
            self.future.set_result(True)
        self.loop.create_task(self._update_flag_states())

    def _writeline(self, data):
        if isinstance(data, str):
            data = codecs.encode(data)
        self.transport.write(data + b'\n')

    async def _update_flag_states(self):
        t0 = time.time()
        if self.flags_success:
            for flag in self.flags_success:
                await self.db.update_submitted(flag)
        if self.flags_pending:
            for flag in self.flags_pending:
                await self.db.update_pending(flag)
        if self.flags_expired:
            for flag in self.flags_expired:
                await self.db.update_expired(flag)
        if self.flags_failed:
            for flag in self.flags_failed:
                await self.db.update_failed(flag)
        # If the connection has been lost prematurely,
        # mark the not yet processed flags as PENDING.
        if self.flags:
            for flag in self.flags:
                await self.db.update_pending(flag)
        self.log.log(LOG_LEVEL_STAT, '[SUBMISSION] [ACCEPTED %d] [PENDING %d] [EXPIRED %d] [UNKNOWN %d]',
            len(self.flags_success),
            len(self.flags_pending + self.flags),
            len(self.flags_expired),
            len(self.flags_failed))
        self.log.log(LOG_LEVEL_STAT, '[GAMESERVER] Updating flag stats took %f seconds', time.time() - t0)
