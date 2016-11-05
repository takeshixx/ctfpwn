"""This module includes everything that is needed to submit flags to
the gameserver."""
import time
import asyncio
import logging

from helperlib.logging import scope_logger

from ctfpwn.flagservice.worker import FlagSubmissionProtocol
from ctfpwn.shared import TooMuchConnectionsException

log = logging.getLogger(__name__)


@scope_logger
class FlagSupervisor(object):
    def __init__(self, db, config, loop=None):
        self.db = db
        self.config = config
        self.submit_interval = self.config.get('flag_submission_interval')
        self.loop = loop or asyncio.get_event_loop()

    def start(self, interval=None):
        if interval:
            self.submit_interval = interval
        async def _run():
            while True:
                await self.submit()
                await asyncio.sleep(self.submit_interval)
        self.loop.create_task(_run())

    def reschedule_submission(self, offset):
        if (self.submit_interval + offset) >= self.config.get('flag_submission_interval_max'):
            self.log.debug('Reached max submission reschedule threshold (%d seconds)',
                           self.config.get('flag_submission_interval_max'))
            self.submit_interval = self.config.get('flag_submission_interval_max')
            return
        self.log.info('Rescheduling submission from %d to %d seconds',
                      self.submit_interval,
                      self.submit_interval + offset)
        self.submit_interval += offset

    def reset_submission_interval(self):
        if self.submit_interval == self.config.get('flag_submission_interval'):
            return
        self.log.info('Rescheduling to default submission (every %d secods)',
                      self.config.get('flag_submission_interval'))
        self.submit_interval = self.config.get('flag_submission_interval')

    async def submit(self):
        """Flag submission job."""
        log.debug('Called submit')
        t0 = time.time()
        flags = await self.db.select_new_and_pending_flags(limit=self.config.get('flag_max_submits'))
        if flags:
            log.info('[SUBMISSION] [COUNT %d]', len(flags))
            future = self.loop.create_future()
            try:
                await self.loop.create_connection(
                    lambda: FlagSubmissionProtocol(flags, self.db, self.config, future),
                    self.config.get('gameserver_host'),
                    self.config.get('gameserver_port'))
                await future
            except ConnectionRefusedError:
                self.log.error('Could not connect to gameserver!')
            except TooMuchConnectionsException:
                self.reschedule_submission(10)
                return
            except Exception as e:
                self.log.exception(e)
                return
            if not future.done():
                future.set_result(False)
            self.reset_submission_interval()
        else:
            log.info('[SUBMISSION] No NEW/PENDING flags for submission...')
        log.debug('Finished flag submission, took %f seconds', time.time() - t0)
