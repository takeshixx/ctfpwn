import sys
import re
import time
import pprint
from twisted.python import log
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, protocol, defer
import txmongo
import txmongo.connection
import txmongo.filter


# Local flag-service settings
SERVICE_PORT = 8081
SERVICE_INTERFACE = '127.0.0.1'
SERVICE_SUBMIT_INTERVAL = 8 # seconds
SERVICE_STATS_INTERVAL = 10 # seconds
SERVICE_MONGO_POOLSIZE = 100

# According to rules, a round is about ~2 min, this corresponds
# to the validity times of flags. But this may vary.
CTF_ROUND_DURATION = 150

# Gameserver settings
GAMESERVER_ADDR = '127.0.0.1'
GAMESERVER_PORT = 9000
GAMESERVER_TIMEOUT = 2
GAMESERVER_CHUNK_SIZE = 10

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


class Flag():
    """
    A class that represents flags, as parsed from incoming lines. See REGEX_INPUT
    and the corresponding input format example.
    """
    def __init__(self,incoming):
        self.service = incoming[0]
        self.target = incoming[1]
        self.flag = incoming[2]
        self.timestamp = int(time.time())


class FlagDB():
    """
    An interface to the database.
    """
    def __init__(self):
        try:
            self.mongo = txmongo.lazyMongoConnectionPool(pool_size=SERVICE_MONGO_POOLSIZE)
            self.db = self.mongo.flagservice
            self.col = self.db.flags
        except Exception as e:
            log.msg('Error in FlagDB().__init__() [EXCEPTION {}]'.format(e))

    @defer.inlineCallbacks
    def insert_new(self, flag):
        """Insert a new flag if it does not already exist, set status to NEW."""
        try:
            yield self.col.update_one(
                {'flag': flag.flag},
                {'$setOnInsert':
                    {
                        'service': flag.service,
                        'target': flag.target,
                        'flag': flag.flag,
                        'state': 'NEW',
                        'comment': '',
                        'timestamp': int(time.time()),
                        'submitted': 0
                    }
                },
                upsert=True
            )
        except Exception as e:
            log.msg(e)

    @defer.inlineCallbacks
    def select_flags(self, limit=0):
        """Return <limit> flags from database. Defaults to all documents."""
        docs = yield self.col.find(limit=limit)
        defer.returnValue(docs)

    @defer.inlineCallbacks
    def select_new_and_pending(self):
        """Return all flags with status new and pending for submission."""
        docs = yield self.col.find({
            '$or': [
                {'state': 'NEW'},
                {'state': 'PENDING'}
            ]},
            fields={'flag': True, '_id': False}
        )
        defer.returnValue([flag.values()[0] for flag in docs])

    @defer.inlineCallbacks
    def update_submitted(self, flag):
        """Submission of flag was successful, set flag as SUBMITTED."""
        yield self.col.update(
            {'flag': flag},
            {'$set':{
                'state': 'SUBMITTED',
                'submitted': int(time.time())
            }}
        )

    @defer.inlineCallbacks
    def update_pending(self, flag):
        """Flags that have been submitted but were not accepted, set them as PENDING
        in order to retry submission."""
        yield self.col.update(
            {'flag': flag},
            {'$set':{
                'state': 'PENDING'
            }}
        )

    @defer.inlineCallbacks
    def update_expired(self, flag):
        """Flags that are EXPIRED, set them as expired, do not try to submit them again."""
        yield self.col.update(
            {'flag': flag},
            {'$set':{
                'state': 'EXPIRED'
            }}
        )

    @defer.inlineCallbacks
    def update_failed(self, flag):
        """Flags that could not be submitted for whatever reason, most likely they are invalid.
        Mark them as FAILED."""
        yield self.col.update(
            {'flag': flag},
            {'$set':{
                'state': 'FAILED'
            }}
        )

    @defer.inlineCallbacks
    def stats(self):
        """Return some stats of the database, like total flags, count of successful or 
        failed submissions and such."""
        stats = dict()
        stats['totalFlags'] = yield self.col.count()
        stats['newCount'] = yield self.col.count({'state': 'NEW'})
        stats['submittedCount'] = yield self.col.count({'state': 'SUBMITTED'})
        stats['expiredCount'] = yield self.col.count({'state': 'EXPIRED'})
        stats['failedCount'] = yield self.col.count({'state': 'FAILED'})
        stats['pendingCount'] = yield self.col.count({'state': 'PENDING'})
        defer.returnValue(stats)


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

    def connectionLost(self, reason):
        """Take action when connection is lost."""
        pass
            

class FlagSubmissionProtocol(protocol.Protocol):
    """
    An interface to the gameserver for submitting flags.
    Every instance may submit one or more flags at once.
    """
    def __init__(self, flags):
        self.flags = flags
        self.current_flag = None
        self.flags_success = []
        self.flags_failed = []
        self.flags_expired = []
        self.flags_pending = []
        self.db = flag_db

    def connectionMade(self):
        """Read unnecessary banners and stuff."""
        print('Connected to gameserver')

    def dataReceived(self, incoming):

        if 'accepted' in incoming:
            print('Flag accepted')
            self.flags_success.append(self.current_flag)
        elif 'corresponding' in incoming:
            print('Service is not available')
            self.flags_pending.append(self.current_flag)
        elif 'expired' in incoming:
            print('Flag expired')
            self.flags_expired.append(self.current_flag)
        elif 'no such flag' in incoming:
            print('Invalid flag')
            self.flags_failed.append(self.current_flag)
        elif 'own flag' in incoming:
            self.flags_failed.append(self.current_flag)
        elif 'too much' in incoming:
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
        #self.db = FlagDB()
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

    def __init__(self, flags):
        self.flags = flags

    def startedConnecting(self, connector):
        pass

    def buildProtocol(self, addr):
        return FlagSubmissionProtocol(self.flags)

    def clientConnectionLost(self, connector, reason):
        print('Connection lost: {}'.format(reason))

    def clientConnectionFailed(self, connector, reason):
        print('Connection to gameserver failed: {}'.format(reason))


@defer.inlineCallbacks
def submit_flags():
    flags = yield flag_db.select_new_and_pending()

    if len(flags):
        print('Trying to submit {} flags'.format(len(flags)))
        reactor.connectTCP(GAMESERVER_ADDR, GAMESERVER_PORT, FlagSubmissionFactory(flags))
    else:
        print('No flags for submission')


@defer.inlineCallbacks
def flag_stats():
    stats = yield flag_db.stats()
    pprint.pprint(stats)
    

def run_service():
    """
    Main function which handles requests and application logic. This function needs to be called
    in order to start the flag-service.
    """
    try:
        log.startLogging(sys.stdout)

        # A global instance. Reduces amount of established sessions to MongoDB.
        global flag_db
        flag_db = FlagDB()

        factory = protocol.ServerFactory()
        factory.protocol = FlagReceiverProtocol
        reactor.listenTCP(SERVICE_PORT,factory,interface=SERVICE_INTERFACE)

        # Try submitting NEW and PENDING flags every SERVICE_RESUBMIT_INTERVAL seconds
        submit = LoopingCall(submit_flags)
        submit.start(SERVICE_SUBMIT_INTERVAL)

        # Print stats every SERVICE_STATS_INTERVAL seconds
        stats = LoopingCall(flag_stats)
        stats.start(SERVICE_STATS_INTERVAL)

        reactor.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        log.msg('Error in main() function! [EXCEPTION {}]'.format(e))

if __name__ == '__main__':
    run_service()
