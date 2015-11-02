import sys
import pprint
from twisted.python import log
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, protocol, defer

from .shared import flag_db
from .flagdb import FlagDB, Flag
from .receiver import FlagReceiverProtocol
from .submitter import FlagSubmissionFactory
from .checker import ServiceChecker

# Local flag-service settings
SERVICE_PORT = 8081
SERVICE_ADDR = '127.0.0.1'

# Gameserver settings
GAMESERVER_ADDR = '127.0.0.1'
GAMESERVER_PORT = 9000

# Interval settings for all jobs
SERVICE_SUBMIT_INTERVAL = 8
SERVICE_STATS_INTERVAL = 15
SERVICE_ALIVE_INTERVAL = 5

# According to rules, a round is about ~2 min, this corresponds
# to the validity times of flags. But this may vary.
CTF_ROUND_DURATION = 150


@defer.inlineCallbacks
def submit_flags():
    """Flag submission job, runs every SERVICE_SUBMIT_INTERVAL seconds."""
    flags = yield flag_db.select_new_and_pending()

    if len(flags):
        print('Trying to submit {} flags'.format(len(flags)))
        reactor.connectTCP(GAMESERVER_ADDR, GAMESERVER_PORT, FlagSubmissionFactory(flags, flag_db))
    else:
        print('No flags for submission')


@defer.inlineCallbacks
def print_flag_stats():
    """Database statistics that will be printed every SERVICE_STATS_INTERVAL seconds."""
    stats = yield flag_db.stats()
    pprint.pprint(stats)


def run_flagservice():
    """
    Main function which handles requests and application logic. This function needs to be called
    in order to start the flag-service.
    """
    try:
        log.startLogging(sys.stdout)

        # Factory for the flag receiver
        factory = protocol.ServerFactory()
        factory.protocol = FlagReceiverProtocol
        reactor.listenTCP(SERVICE_PORT,factory,interface=SERVICE_ADDR)

        # Update states of known services every SERVICE_ALIVE_INTERVAL seconds.
        checker = ServiceChecker()
        checker.start(SERVICE_ALIVE_INTERVAL)

        # Try submitting NEW and PENDING flags every SERVICE_RESUBMIT_INTERVAL seconds.
        submit = LoopingCall(submit_flags)
        submit.start(SERVICE_SUBMIT_INTERVAL)

        # Print stats every SERVICE_STATS_INTERVAL seconds.
        stats = LoopingCall(print_flag_stats)
        stats.start(SERVICE_STATS_INTERVAL)

        reactor.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        log.msg('Error in main() function! [EXCEPTION {}]'.format(e))

if __name__ == '__main__':
    run_flagservice()