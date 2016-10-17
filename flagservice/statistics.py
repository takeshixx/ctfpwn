import time

from helperlib.logging import scope_logger
from twisted.internet import defer
from twisted.internet.task import LoopingCall

from .shared import flag_db, LOG_LEVEL_STAT

@scope_logger
class Statistics(LoopingCall):
    """
    Database statistics that will be printed every SERVICE_STATS_INTERVAL seconds.
    """
    def __init__(self, *args, **kwargs):
        super(Statistics, self).__init__(self.callback, *args, **kwargs)

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