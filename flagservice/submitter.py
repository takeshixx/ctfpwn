"""This module includes everything that is needed to submit flags to
the gameserver."""
from twisted.internet import protocol

# Messages by the gameserver, need to be adjusted
GAME_SERVER_MSG_SUCCESS = 'accepted'
GAME_SERVER_MSG_EXPIRED = 'expired'
GAME_SERVER_MSG_SERVICE_DOWN = 'corresponding'
GAME_SERVER_MSG_INVALID = 'no such flag'
GAME_SERVER_MSG_OWN_FLAG = 'own flag'
GAME_SERVER_MSG_TOO_MUCH = 'too much'

class FlagSubmissionProtocol(protocol.Protocol):
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
        print('Connected to gameserver')

    def dataReceived(self, incoming):

        if GAME_SERVER_MSG_SUCCESS in incoming:
            print('Flag accepted')
            self.flags_success.append(self.current_flag)
        elif GAME_SERVER_MSG_SERVICE_DOWN in incoming:
            print('Service is not available')
            self.flags_pending.append(self.current_flag)
        elif GAME_SERVER_MSG_EXPIRED in incoming:
            print('Flag expired')
            self.flags_expired.append(self.current_flag)
        elif GAME_SERVER_MSG_INVALID in incoming:
            print('Invalid flag')
            self.flags_failed.append(self.current_flag)
        elif GAME_SERVER_MSG_OWN_FLAG in incoming:
            self.flags_failed.append(self.current_flag)
        elif GAME_SERVER_MSG_TOO_MUCH in incoming:
            """TODO: The gameserver may complains about too much connections from our team.
            This message has to be adjusted. Abort the current session and retry the current
            flags in the next iteration."""
            self.transport.loseConnection()
            return
        else:
            print('Unknown gameserver message: {}'.format(incoming))

        if not len(self.flags):
            self.transport.loseConnection()
            return

        self.current_flag = self.flags.pop(0)
        self._write_line(self.current_flag)

    def connectionLost(self, reason):
        self._update_flag_states()

    def _write_line(self, line):
        self.transport.write('{}\n'.format(line))

    def _update_flag_states(self):

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
        print('Connection lost: {}'.format(reason))

    def clientConnectionFailed(self, connector, reason):
        print('Connection to gameserver failed: {}'.format(reason))