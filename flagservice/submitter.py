"""This module includes everything that is needed to submit flags to
the gameserver."""
import time
from twisted.internet import protocol
from twisted.protocols import policies
from helperlib.logging import scope_logger

from .shared import LOG_LEVEL_STAT


# Messages by the gameserver, need to be adjusted
GAME_SERVER_MSG_SUCCESS = b'accepted'
GAME_SERVER_MSG_SUCCESS2 = b'congratulations'
GAME_SERVER_MSG_EXPIRED = b'expired'
GAME_SERVER_MSG_SERVICE_DOWN = b'corresponding'
GAME_SERVER_MSG_INVALID = b'no such flag'
GAME_SERVER_MSG_OWN_FLAG = b'own flag'
GAME_SERVER_MSG_TOO_MUCH = b'too much'
GAME_SERVER_MSG_ALREADY_SUBMITTED = b'already submitted'


@scope_logger
class FlagSubmissionProtocol(protocol.Protocol, policies.TimeoutMixin):
    """
    An interface to the gameserver for submitting flags.
    Every instance may submit one or more flags at once.
    """
    def __init__(self, flags, flag_db):
        self.flags = flags
        self.db = flag_db
        self.current_flag = None
        self.flags_success = []
        self.flags_failed = []
        self.flags_expired = []
        self.flags_pending = []

    def connectionMade(self):
        """Read unnecessary banners and stuff."""
        self.log.debug('[GAMESERVER] [CONNECTED]')
        self.setTimeout(5)

    def timeoutConnection(self):
        self.transport.abortConnection()

    def dataReceived(self, incoming):
        self.resetTimeout()

        if GAME_SERVER_MSG_SUCCESS in incoming or GAME_SERVER_MSG_SUCCESS2 in incoming:
            # log.score('[{}] [FLAG {}] [TARGET {}] [CAPTURED {}]'.format(
            #     self.current_flag.get('service'),
            #     self.current_flag.get('flag'),
            #     self.current_flag.get('target'),
            #     datetime.datetime.fromtimestamp(self.current_flag.get('timestamp')).strftime('%H:%M:%S')
            # ))
            self.flags_success.append(self.current_flag.get('flag'))
        elif GAME_SERVER_MSG_SERVICE_DOWN in incoming:
            self.log.error('[%s] [GAMESERVER REPORTED SERVICE NOT AVAILABLE]',
                self.current_flag.get('service')
            )
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
            self.transport.loseConnection()
            return
        else:
            self.log.warning('Unknown gameserver message: %r', incoming.strip())

        if not len(self.flags):
            self.transport.loseConnection()
            return

        self.current_flag = self.flags.pop(0)
        self._write_line(self.current_flag.get('flag'))

    def connectionLost(self, reason):
        self._update_flag_states()

    def _write_line(self, line):
        self.resetTimeout()
        self.transport.write('{}\n'.format(line).encode('utf-8'))

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

        """If the connection has been lost prematurely, mark the not yet
        processed flags as PENDING."""
        if self.flags:
            for flag in self.flags:
                self.db.update_pending(flag)

        self.log.log(LOG_LEVEL_STAT, '[SUBMIT] [ACCEPTED %d] [PENDING %d] [EXPIRED %d] [UNKNOWN %d]',
            len(self.flags_success),
            len(self.flags_pending + self.flags),
            len(self.flags_expired),
            len(self.flags_failed)
        )
        self.log.log(LOG_LEVEL_STAT, '[GAMESERVER] _update_flag_states() took %f', time.time() - t0)


@scope_logger
class FlagSubmissionFactory(protocol.Factory):
    protocol = FlagSubmissionProtocol

    def __init__(self, flags, flag_db):
        self.flags = flags
        self.db = flag_db

    def startedConnecting(self, connector):
        pass

    def buildProtocol(self, address):
        return FlagSubmissionProtocol(self.flags, self.db)

    def clientConnectionLost(self, connector, reason):
        self.log.info('[GAMESERVER] [CONNECTION LOST] [REASON %s]', reason.getErrorMessage())

    def clientConnectionFailed(self, connector, reason):
        self.log.error('[GAMESERVER] [CONNECTION FAILED] [REASON %s]', reason.getErrorMessage())
