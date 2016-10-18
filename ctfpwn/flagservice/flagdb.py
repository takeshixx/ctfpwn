"""This module provides an interface to the database and
anything that is needed to handle flags."""
import logging
import time
import motor.motor_asyncio
import pymongo

from helperlib.logging import scope_logger

# TODO: move to config file
SERVICE_MONGO_POOLSIZE = 100
log = logging.getLogger(__name__)


@scope_logger
class FlagDB(object):
    """An interface to the database."""
    def __init__(self):
        try:
            self.mongo = motor.motor_asyncio.AsyncIOMotorClient()
            self.db = self.mongo.flagservice
            self.col_flags = self.db.flags
            self.col_services = self.db.services
        except Exception as e:
            self.log.exception(e)

    @classmethod
    async def create(cls):
        obj = cls()
        await obj.setup_database_indexes()
        return obj

    async def setup_database_indexes(self):
        """Speed up find queries by creating indexes."""
        await self.col_flags.create_index([('flag', pymongo.ASCENDING)])
        await self.col_flags.create_index([('state', pymongo.ASCENDING)])

    async def insert_new(self, flag):
        """Insert a new flag if it does not already exist,
        set status to NEW."""
        try:
            return await self.col_flags.update_one(
                {'flag': flag.flag},
                {'$setOnInsert':
                    {'service': flag.service,
                     'target': flag.target,
                     'flag': flag.flag,
                     'state': 'NEW',
                     'comment': '',
                     'timestamp': int(time.time()),
                     'submitted': 0}}, upsert=True)
        except Exception as e:
            self.log.debug(e)

    async def select_flags(self, limit=0):
        """Return <limit> flags from database. Defaults
        to all documents."""
        try:
            return self.col_flags.find(limit=limit)
        except Exception as e:
            self.log.debug(e)

    async def select_new_and_pending(self, limit=100):
        """Return all flags with status new and pending
        for submission."""
        try:
            return self.col_flags.find({
                '$or': [{'state': 'NEW'},
                        {'state': 'PENDING'}]},
                limit=limit)
        except Exception as e:
            self.log.debug(e)

    async def update_submitted(self, flag):
        """Submission of flag was successful, set flag
        as SUBMITTED."""
        try:
            return await self.col_flags.update(
                {'flag': flag},
                {'$set': {
                    'state': 'SUBMITTED',
                    'submitted': int(time.time())}})
        except Exception as e:
            self.log.debug(e)

    async def update_pending(self, flag):
        """Flags that have been submitted but were not
        accepted, set them as PENDING in order to retry
        submission."""
        try:
            return await self.col_flags.update(
                {'flag': flag},
                {'$set': {'state': 'PENDING'}})
        except Exception as e:
            self.log.debug(e)

    async def update_expired(self, flag):
        """Flags that are EXPIRED, set them as expired,
        do not try to submit them again."""
        try:
            return await self.col_flags.update(
                {'flag': flag},
                {'$set': {'state': 'EXPIRED'}})
        except Exception as e:
            self.log.debug(e)

    async def update_failed(self, flag):
        """Flags that could not be submitted for whatever
        reason, most likely they are invalid. Mark them as
        FAILED."""
        try:
            return await self.col_flags.update(
                {'flag': flag},
                {'$set': {'state': 'FAILED'}})
        except Exception as e:
            self.log.debug(e)

    async def insert_service(self, service):
        """Insert a new service if it does not yet exist."""
        try:
            return await self.col_services.update_one(
                {'name': service.name},
                {'$setOnInsert':
                    {'name': service.name,
                     'host': service.host,
                     'port': service.port,
                     'state': service.state,
                     'changed': int(time.time()),
                     'comment': service.comment,
                     'timestamp': int(time.time())
                }}, upsert=True)
        except Exception as e:
            self.log.debug(e)

    async def update_service_up(self, service):
        """Update a service, set state to UP."""
        try:
            return await self.col_services.update(
                {'name': service.name},
                {'$set': {'state': 'UP',
                          'changed': int(time.time())}})
        except Exception as e:
            self.log.debug(e)

    async def update_service_down(self, service):
        """Update a service, set state to DOWN."""
        try:
            return self.col_services.update(
                {'name': service.name},
                {'$set': {'state': 'DOWN',
                          'changed': int(time.time())}})
        except Exception as e:
            self.log.debug(e)

    async def select_services(self, limit=0):
        """Return <limit> services from database. Defaults
        to all services."""
        try:
            return self.col_services.find(limit=limit)
        except Exception as e:
            self.log.debug(e)

    async def stats(self):
        """Return some stats of the database, like total
        flags, count of successful or failed submissions and such."""
        try:
            stats = dict()
            stats['totalFlags'] = await self.col_flags.count()
            stats['newCount'] = await self.col_flags.count({'state': 'NEW'})
            stats['submittedCount'] = await self.col_flags.count({'state': 'SUBMITTED'})
            stats['expiredCount'] = await self.col_flags.count({'state': 'EXPIRED'})
            stats['failedCount'] = await self.col_flags.count({'state': 'FAILED'})
            stats['pendingCount'] = await self.col_flags.count({'state': 'PENDING'})
            return stats
        except Exception as e:
            self.log.debug(e)
