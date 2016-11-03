"""This module includes everything that is needed to submit flags to
the gameserver."""
import time
import asyncio
import logging

from helperlib.logging import scope_logger

from ctfpwn.flagservice.worker import FlagSubmissionProtocol

log = logging.getLogger(__name__)


@scope_logger
class FlagSupervisor(object):
    def __init__(self, db, config, loop=None):
        self.db = db
        self.config = config
        self.loop = loop or asyncio.get_event_loop()

    def start(self, interval):
        async def _run(interval):
            while True:
                await self.submit()
                await asyncio.sleep(interval)
        self.loop.create_task(_run(interval))

    async def submit(self):
        """Flag submission job, runs every SERVICE_SUBMIT_INTERVAL
        seconds."""
        log.debug('Called submit')
        t0 = time.time()
        flags = await self.db.select_new_and_pending_flags(limit=self.config.get('flag_max_submits'))
        if flags:
            log.info('[SUBMIT] [COUNT %d]', len(flags))
            self.loop.create_connection(lambda: FlagSubmissionProtocol(flags, self.db, self.config),
                                   self.config.get('gameserver_host'),
                                   self.config.get('gameserver_port'))
        else:
            log.info('[SUBMIT] No NEW/PENDING flags for submission...')
        log.debug('Finished submitter(), took %f', time.time() - t0)
