"""This module provides an interface to the database and
anything that is needed to handle exploits."""
import time
import logging
# import asyncio
import motor.motor_asyncio
import pymongo
from helperlib.logging import scope_logger

log = logging.getLogger(__name__)

LOG_LEVEL_STAT = logging.INFO + 1
logging.addLevelName(LOG_LEVEL_STAT, 'STATISTIC')

# Maximum amount of simultaneous connections to the database
SERVICE_MONGO_POOLSIZE = 100


@scope_logger
class CtfDb():
    """An interface to the database. It provides methods
    to add/remove exploits and exploit runs and also for
    storing new flags in the database."""
    def __init__(self):
        try:
            # TODO: one time connect instead of every instance?
            self.mongo = motor.motor_asyncio.AsyncIOMotorClient()
            self.exploitdb = self.mongo.exploitservice
            self.col_expl = self.exploitdb.exploits
            self.col_runs = self.exploitdb.runs
            self.col_targets = self.exploitdb.targets
            self.flagdb = self.mongo.flagservice
            self.col_flags = self.flagdb.flags
            self.col_services = self.flagdb.services
        except Exception as e:
            self.log.error('Error in ExploitDB().__init__() [EXCEPTION %s]', str(e))

    @classmethod
    async def create(cls):
        obj = cls()
        await obj.setup_database_indexes()
        return obj

    async def setup_database_indexes(self):
        """Speed up find queries by creating indexes."""
        await self.col_flags.create_index([('flag', pymongo.ASCENDING)])
        await self.col_flags.create_index([('state', pymongo.ASCENDING)])

    async def insert_new_flag(self, flag):
        """Insert a new flag if it does not already exist, set status to NEW."""
        try:
            return await self.col_flags.update(
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

    async def select_exploits(self, limit=0):
        try:
            cursor = self.col_expl.find(limit=limit)
            return await cursor.to_list(None)
        except Exception as e:
            self.log.debug(e)

    async def select_exploits_enabled(self):
        try:
            cursor = self.col_expl.find({'enabled': True})
            return await cursor.to_list(None)
        except Exception as e:
            self.log.debug(e)

    async def select_exploit_services(self, limit=0):
        try:
            cursor = self.col_expl.distinct('port')
            return await cursor.to_list(None)
        except Exception as e:
            self.log.debug(e)

    async def select_alive_targets(self):
        try:
            cursor = self.col_targets.find({'alive': True})
            return await cursor.to_list(None)
        except Exception as e:
            self.log.debug(e)

    async def update_target(self, target, alive):
        try:
            return self.col_targets.update(
                {'host': target}, {'$set': {'alive': alive}}, upsert=True)
        except Exception as e:
            self.log.exception(e)

    async def update_target_services(self, target, services):
        try:
            return await self.col_targets.update(
                {'host': target}, {'$set': {'services': services}}, upsert=True)
        except Exception as e:
            self.log.exception(e)

    async def update_exploit(self, service, exploit, port, enabled):
        """Enable/Disable and exploit. If the exploit does not exists, it will be created."""
        try:
            return await self.col_expl.update(
                    {'service': service,
                     'exploit': exploit,
                     'port': port},
                    {'$set': {'service': service,
                              'exploit': exploit,
                              'port': port,
                              'enabled': enabled}}, upsert=True)
        except Exception as e:
            self.log.debug(e)

    async def insert_run(self, service, exploit, target, port, state, started, finished):
        try:
            return await self.col_runs.insert({
                'service': service,
                'exploit': exploit,
                'target': target,
                'port': port,
                'state': state,
                'started': started,
                'finished': finished})
        except Exception as e:
            self.log.debug(e)

    async def select_flags(self, limit=0):
        """Return <limit> flags from database. Defaults
        to all documents."""
        try:
            cursor = self.col_flags.find(limit=limit)
            return await cursor.to_list(None)
        except Exception as e:
            self.log.debug(e)

    async def select_new_and_pending_flags(self, limit=100):
        """Return all flags with status new and pending
        for submission."""
        try:
            cursor = self.col_flags.find({
                        '$or': [{'state': 'NEW'},
                                {'state': 'PENDING'}]}, limit=limit)
            return await cursor.to_list(None)
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
            cursor = self.col_services.find(limit=limit)
            return await cursor.to_list(None)
        except Exception as e:
            self.log.debug(e)

    async def exploit_stats(self):
        """Print available exploit, just for test purposes."""
        try:
            exploits = await self.select_exploits()
            exploits = len(exploits)
            exploits_enabled = await self.select_exploits_enabled()
            exploits_enabled = len(exploits_enabled)
            self.log.log(LOG_LEVEL_STAT, '[EXPLOITS] [AVAILABLE %d] [ENABLED %d]', exploits, exploits_enabled)
            targets = await self.select_alive_targets()
            targets = len(targets)
            self.log.log(LOG_LEVEL_STAT, '[TARGETS] [ALIVE %d]', targets)
        except Exception as e:
            self.log.debug(e)

    async def flag_stats(self):
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
