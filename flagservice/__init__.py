#!/usr/bin/env python3
import sys
import time
import logging
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, protocol, defer
from helperlib.logging import scope_logger, default_config, load_config

from .shared import flag_db, LOG_LEVEL_STAT
from .receiver import FlagReceiverProtocol
from .submitter import FlagSubmissionFactory

log = logging.getLogger(__name__)

# Local flag-service settings
SERVICE_PORT = 8081
SERVICE_ADDR = '127.0.0.1'

# Gameserver settings
GAMESERVER_ADDR = '127.0.0.1'
GAMESERVER_PORT = 9000

# Interval settings for all jobs
SERVICE_SUBMIT_INTERVAL = 12
SERVICE_STATS_INTERVAL = 5

# According to rules, a round is about ~2 min, this corresponds
# to the validity times of flags. But this may vary.
CTF_ROUND_DURATION = 120

# How many flags should be submitted at the same time at max.
MAX_FLAG_SUBMITS = 1000


@scope_logger
class Submitter(LoopingCall):
    """
    Flag submission job, runs every SERVICE_SUBMIT_INTERVAL seconds.
    """
    def __init__(self, *args, **kwargs):
        super(Submitter, self).__init__(self.callback, *args, **kwargs)

    @defer.inlineCallbacks
    def callback(self):
        self.log.debug('started Submitter.callback()')
        t0 = time.time()
        try:
            flags = yield flag_db.select_new_and_pending(limit=MAX_FLAG_SUBMITS)

            if flags:
                self.log.info('[SUBMIT] [COUNT %d]', len(flags))
                reactor.connectTCP(GAMESERVER_ADDR, GAMESERVER_PORT, FlagSubmissionFactory(flags, flag_db))
            else:
                self.log.info('[SUBMIT] No NEW/PENDING flags for submission...')
        except Exception as e:
            self.log.warning(e)

        self.log.debug('finished Submitter.callback() took %f', time.time() - t0)


@scope_logger
class Stats(LoopingCall):
    """
    Database statistics that will be printed every SERVICE_STATS_INTERVAL seconds.
    """
    def __init__(self, *args, **kwargs):
        super(Stats, self).__init__(self.callback, *args, **kwargs)

    @defer.inlineCallbacks
    def callback(self):
        self.log.debug('started Stats.callback()')
        t0 = time.time()
        try:
            stats = yield flag_db.stats()
            self.log.log(LOG_LEVEL_STAT, '[FLAGS] [TOTAL %d] [SUBMITTED %d] [EXPIRED %d] [FAILED %d] [NEW %d] [PENDING %d]',
                stats.get('totalFlags'),
                stats.get('submittedCount'),
                stats.get('expiredCount'),
                stats.get('failedCount'),
                stats.get('newCount'),
                stats.get('pendingCount')
            )
        except Exception as e:
            self.log.warning(e)

        self.log.debug('finished Stats.callback() took %f', time.time() - t0)


def run_flagservice():
    """
    Main function which handles requests and application logic. This function needs to be called
    in order to start the flag-service.
    """
    default_config(level=logging.DEBUG, disable_existing_loggers=False)
    try:
        load_config('flagservice.ini')
    except Exception as e:
        log.warning('No logging config file flagservice.ini found. Using default')

    try:
        log.info('Starting flagservice')
        # Factory for the flag receiver
        factory = protocol.ServerFactory()
        factory.protocol = FlagReceiverProtocol
        reactor.listenTCP(SERVICE_PORT, factory, interface=SERVICE_ADDR)

        # Print stats every SERVICE_STATS_INTERVAL seconds.
        stats = Stats()
        stats.start(SERVICE_STATS_INTERVAL, now=True)

        # Update states of known services every SERVICE_ALIVE_INTERVAL seconds.
        # checker = ServiceChecker()
        # checker.start(SERVICE_ALIVE_INTERVAL)

        # Try submitting NEW and PENDING flags every SERVICE_RESUBMIT_INTERVAL seconds.
        submit = Submitter()
        submit.start(SERVICE_SUBMIT_INTERVAL, now=True)

        reactor.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        log.exception('Error in main() function! [EXCEPTION %s]', e)

if __name__ == '__main__':
    run_flagservice()
