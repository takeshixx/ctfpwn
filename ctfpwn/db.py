"""This module provides an interface to the database and
anything that is needed to handle exploits, flags and targets."""
import time
import datetime
import logging
import motor.motor_asyncio
import pymongo
from helperlib.logging import scope_logger

log = logging.getLogger(__name__)
LOG_LEVEL_STAT = logging.INFO + 1
logging.addLevelName(LOG_LEVEL_STAT, 'STATISTIC')


@scope_logger
class CtfDb():
    """An interface to the database. It provides methods
    to add/remove exploits and exploit runs and also for
    storing new flags in the database."""
    def __init__(self, config=None):
        self.config = config
        if not self.config:
            host = '127.0.0.1'
            port = 27017
        else:
            host = self.config['database']['host']
            port = self.config['database']['port']
        try:
            # TODO: one time connect instead of every instance?
            self.mongo = motor.motor_asyncio.AsyncIOMotorClient(host, port)
            self.ctfdb = self.mongo.ctfdb
            self.exploits = self.ctfdb.exploits
            self.exploit_runs = self.ctfdb.runs
            self.targets = self.ctfdb.targets
            self.flags = self.ctfdb.flags
            self.services = self.ctfdb.services
        except Exception as e:
            self.log.exception(e)

    @classmethod
    async def create(cls, config=None):
        obj = cls(config)
        await obj.setup_database_indexes()
        return obj

    async def setup_database_indexes(self):
        """Speed up find queries by creating indexes."""
        await self.flags.create_index([('flag', pymongo.ASCENDING)])
        await self.flags.create_index([('state', pymongo.ASCENDING)])

    async def insert_new_flag(self, flag):
        """Insert a new flag if it does not already exist, set status to NEW."""
        try:
            return await self.flags.update(
                {'flag': flag.flag},
                {'$setOnInsert':
                    {'service': flag.service,
                     'target': flag.target,
                     'flag': flag.flag,
                     'state': 'NEW',
                     'comment': '',
                     'timestamp': datetime.datetime.utcnow(),
                     'submitted': 0}}, upsert=True)
        except Exception as e:
            self.log.exception(e)

    async def select_exploits(self, limit=0):
        try:
            cursor = self.exploits.find(limit=limit)
            return await cursor.to_list(None)
        except Exception as e:
            self.log.exception(e)

    async def select_exploits_enabled(self):
        try:
            cursor = self.exploits.find({'enabled': True})
            return await cursor.to_list(None)
        except Exception as e:
            self.log.exception(e)

    async def select_exploit_services(self, limit=0):
        try:
            cursor = self.exploits.distinct('port')
            return await cursor.to_list(None)
        except Exception as e:
            self.log.exception(e)

    async def select_alive_targets(self):
        try:
            cursor = self.targets.find({'alive': True})
            return await cursor.to_list(None)
        except Exception as e:
            self.log.exception(e)

    async def update_target(self, target, alive):
        try:
            return self.targets.update(
                {'host': target},
                {'$set': {'alive': alive, 'timestamp': datetime.datetime.utcnow()}}, upsert=True)
        except Exception as e:
            self.log.exception(e)

    async def update_target_services(self, target, services):
        try:
            # services should be a live of object IDs
            if not isinstance(services, list):
                self.log.error('services should be a list of object IDs')
            return await self.targets.update(
                {'host': target},
                {'$set': {'services': services, 'timestamp': datetime.datetime.utcnow()}}, upsert=True)
        except Exception as e:
            self.log.exception(e)

    async def insert_service(self, service):
        """Insert a new service if it does not yet exist."""
        try:
            return await self.services.update(
                    {'name': service.name},
                    {'$set':
                        {'name': service.name,
                         'type': service.type,
                         'port': service.port,
                         'url': service.url,
                         'meta': service.meta,
                         'timestamp': datetime.datetime.utcnow()}},
                    upsert=True)
        except Exception as e:
            self.log.exception(e)

    async def select_all_services(self, limit=0):
        """Return <limit> services from database. Defaults
        to all services."""
        try:
            cursor = self.services.find(limit=limit)
            return await cursor.to_list(None)
        except Exception as e:
            self.log.exception(e)

    async def select_services(self, service_type='port', limit=0):
        """Return <limit> services from database. Defaults
        to all services."""
        try:
            cursor = self.services.find({'type': service_type}, limit=limit)
            return await cursor.to_list(None)
        except Exception as e:
            self.log.exception(e)

    async def delete_service(self, service_name):
        """Delete a service by it's name."""
        try:
            return await self.services.remove({'name': service_name})
        except Exception as e:
            self.log.exception(e)

    async def update_exploit(self, service, exploit, port, enabled):
        """Enable/Disable and exploit. If the exploit does not exists, it will be created."""
        try:
            return await self.exploits.update(
                    {'service': service,
                     'exploit': exploit,
                     'port': port},
                    {'$set': {'service': service,
                              'exploit': exploit,
                              'port': port,
                              'enabled': enabled,
                              'timestamp': datetime.datetime.utcnow()}}, upsert=True)
        except Exception as e:
            self.log.exception(e)

    async def delete_exploit(self, service_name):
        """Delete a exploit by it's service name."""
        try:
            return await self.exploits.remove({'service': service_name})
        except Exception as e:
            self.log.exception(e)

    async def insert_run(self, service, exploit, target, started,
                         finished, state):
        try:
            return await self.exploit_runs.insert({
                'service': service,
                'exploit': exploit,
                'target': target,
                'started': started,
                'finished': finished,
                'state': state,
                'timestamp': datetime.datetime.utcnow()})
        except Exception as e:
            self.log.exception(e)

    async def select_flags(self, limit=0):
        """Return <limit> flags from database. Defaults
        to all documents."""
        try:
            cursor = self.flags.find(limit=limit)
            return await cursor.to_list(None)
        except Exception as e:
            self.log.exception(e)

    async def select_new_and_pending_flags(self, limit=100):
        """Return all flags with status new and pending
        for submission."""
        try:
            cursor = self.flags.find({
                        '$or': [{'state': 'NEW'},
                                {'state': 'PENDING'}]}, limit=limit)
            return await cursor.to_list(None)
        except Exception as e:
            self.log.exception(e)

    async def update_submitted(self, flag):
        """Submission of flag was successful, set flag
        as SUBMITTED."""
        try:
            return await self.flags.update(
                    {'flag': flag},
                    {'$set': {'state': 'SUBMITTED',
                              'submitted': int(time.time())}})
        except Exception as e:
            self.log.exception(e)

    async def update_pending(self, flag):
        """Flags that have been submitted but were not
        accepted, set them as PENDING in order to retry
        submission."""
        try:
            return await self.flags.update(
                    {'flag': flag},
                    {'$set': {'state': 'PENDING'}})
        except Exception as e:
            self.log.exception(e)

    async def update_expired(self, flag):
        """Flags that are EXPIRED, set them as expired,
        do not try to submit them again."""
        try:
            return await self.flags.update(
                    {'flag': flag},
                    {'$set': {'state': 'EXPIRED'}})
        except Exception as e:
            self.log.exception(e)

    async def update_failed(self, flag):
        """Flags that could not be submitted for whatever
        reason, most likely they are invalid. Mark them as
        FAILED."""
        try:
            return await self.flags.update(
                    {'flag': flag},
                    {'$set': {'state': 'FAILED'}})
        except Exception as e:
            self.log.exception(e)

    async def exploit_stats(self):
        """Print available exploit, just for test purposes."""
        try:
            exploits = await self.select_exploits()
            exploits = len(exploits)
            exploits_enabled = await self.select_exploits_enabled()
            exploits_enabled = len(exploits_enabled)
            self.log.log(LOG_LEVEL_STAT, '[AVAILABLE %d] [ENABLED %d]', exploits, exploits_enabled)
        except Exception as e:
            self.log.exception(e)

    async def targets_stats(self):
        """Print stats for targets in database."""
        try:
            targets = await self.select_alive_targets()
            targets = len(targets)
            self.log.log(LOG_LEVEL_STAT, '[ALIVE %d]', targets)
        except Exception as e:
            self.log.exception(e)

    async def flag_stats(self):
        """Return some stats of the database, like total
        flags, count of successful or failed submissions and such."""
        try:
            stats = dict()
            stats['totalFlags'] = await self.flags.find().count()
            stats['newCount'] = await self.flags.find({'state': 'NEW'}).count()
            stats['submittedCount'] = await self.flags.find({'state': 'SUBMITTED'}).count()
            stats['expiredCount'] = await self.flags.find({'state': 'EXPIRED'}).count()
            stats['failedCount'] = await self.flags.find({'state': 'FAILED'}).count()
            stats['pendingCount'] = await self.flags.find({'state': 'PENDING'}).count()
            return stats
        except Exception as e:
            self.log.exception(e)
