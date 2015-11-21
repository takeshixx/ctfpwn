"""This module provides an interface to the database and
anything that is needed to handle flags."""
import time
import txmongo
import txmongo.connection
import txmongo.filter
from twisted.internet import defer

from .tinylogs import log

SERVICE_MONGO_POOLSIZE = 100

class Flag():
    """A class that represents flags, as parsed from incoming lines. See REGEX_INPUT
    and the corresponding input format example."""
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
            self.col_services = self.db.services
            self.setup_database_indexes()
        except Exception as e:
            log.error('Error in FlagDB().__init__() [EXCEPTION {}]'.format(e))

    @defer.inlineCallbacks
    def setup_database_indexes(self):
        """Speed up find queries by creating indexes."""
        yield self.col.create_index(txmongo.filter.sort(txmongo.filter.ASCENDING('flag')))
        yield self.col.create_index(txmongo.filter.sort(txmongo.filter.ASCENDING('state')))

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
            log.debug(e)

    @defer.inlineCallbacks
    def select_flags(self, limit=0):
        """Return <limit> flags from database. Defaults to all documents."""
        try:
            docs = yield self.col.find(limit=limit)
            defer.returnValue(docs)
        except Exception as e:
            log.debug(e)

    @defer.inlineCallbacks
    def select_new_and_pending(self, limit=100):
        """Return all flags with status new and pending for submission."""
        try:
            flags = yield self.col.find({
                '$or': [
                    {'state': 'NEW'},
                    {'state': 'PENDING'}
                ]},
                limit=limit
            )
            defer.returnValue(flags)
        except Exception as e:
            log.debug(e)

    @defer.inlineCallbacks
    def update_submitted(self, flag):
        """Submission of flag was successful, set flag as SUBMITTED."""
        try:
            yield self.col.update(
                {'flag': flag},
                {'$set':{
                    'state': 'SUBMITTED',
                    'submitted': int(time.time())
                }}
            )
        except Exception as e:
            log.debug(e)

    @defer.inlineCallbacks
    def update_pending(self, flag):
        """Flags that have been submitted but were not accepted, set them as PENDING
        in order to retry submission."""
        try:
            yield self.col.update(
                {'flag': flag},
                {'$set':{
                    'state': 'PENDING'
                }}
            )
        except Exception as e:
            log.debug(e)

    @defer.inlineCallbacks
    def update_expired(self, flag):
        """Flags that are EXPIRED, set them as expired, do not try to submit them again."""
        try:
            yield self.col.update(
                {'flag': flag},
                {'$set':{
                    'state': 'EXPIRED'
                }}
            )
        except Exception as e:
            log.debug(e)

    @defer.inlineCallbacks
    def update_failed(self, flag):
        """Flags that could not be submitted for whatever reason, most likely they are invalid.
        Mark them as FAILED."""
        try:
            yield self.col.update(
                {'flag': flag},
                {'$set':{
                    'state': 'FAILED'
                }}
            )
        except Exception as e:
            log.debug(e)

    @defer.inlineCallbacks
    def insert_service(self, service):
        """Insert a new service if it does not yet exist."""
        try:
            yield self.col_services.update_one(
                {'name': service.name},
                {'$setOnInsert':
                    {
                        'name': service.name,
                        'host': service.host,
                        'port': service.port,
                        'state': service.state,
                        'changed': int(time.time()),
                        'comment': service.comment,
                        'timestamp': int(time.time())
                    }
                },
                upsert=True
            )
        except Exception as e:
            log.debug(e)

    @defer.inlineCallbacks
    def update_service_up(self, service):
        """Update a service, set state to UP."""
        try:
            yield self.col_services.update(
                {'name': service.name},
                {'$set':{
                    'state': 'UP',
                    'changed': int(time.time())
                }}
            )
        except Exception as e:
            log.debug(e)

    @defer.inlineCallbacks
    def update_service_down(self, service):
        """Update a service, set state to DOWN."""
        try:
            yield self.col_services.update(
                {'name': service.name},
                {'$set':{
                    'state': 'DOWN',
                    'changed': int(time.time())
                }}
            )
        except Exception as e:
            log.debug(e)

    @defer.inlineCallbacks
    def select_services(self, limit=0):
        """Return <limit> services from database. Defaults to all services."""
        try:
            services = yield self.col_services.find(limit=limit)
            defer.returnValue(services)
        except Exception as e:
            log.debug(e)

    @defer.inlineCallbacks
    def stats(self):
        """Return some stats of the database, like total flags, count of successful or
        failed submissions and such."""
        try:
            stats = dict()
            stats['totalFlags'] = yield self.col.count()
            stats['newCount'] = yield self.col.count({'state': 'NEW'})
            stats['submittedCount'] = yield self.col.count({'state': 'SUBMITTED'})
            stats['expiredCount'] = yield self.col.count({'state': 'EXPIRED'})
            stats['failedCount'] = yield self.col.count({'state': 'FAILED'})
            stats['pendingCount'] = yield self.col.count({'state': 'PENDING'})
            defer.returnValue(stats)
        except Exception as e:
            log.debug(e)