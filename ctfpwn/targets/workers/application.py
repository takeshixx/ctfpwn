import asyncio
import aiohttp
import random

from helperlib.logging import scope_logger

USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
               'Mozilla/5.0 (X11; Linux i686; rv:30.0) Gecko/20100101 Firefox/30.0',
               'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
               'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11) AppleWebKit/601.1.39 (KHTML, like Gecko) Version/9.0 Safari/601.1.39']


@scope_logger
class HttpWorker(object):
    def __init__(self, db, loop=None):
        self.db = db
        self.loop = loop or asyncio.get_event_loop()
        self.target = None
        self.services = None
        self.alive_services = list()
        self.futures = list()

    async def check_target_urls(self, target, services):
        """Check a single target IP for running services."""
        self.log.debug('Checking %d service URLs on target %s',
                       len(services),
                       target.get('host'))
        self.target = target
        self.services = services
        for service in self.services:
            f = self.loop.create_task(self.check_url(service))
            self.futures.append(f)
        await asyncio.wait(self.futures)
        self.log.info('Found %d running service(s) on target %s',
                      len(self.alive_services),
                      target.get('host'))
        self.loop.create_task(self.db.update_target_services(
            target.get('host'),
            self.alive_services))

    async def check_url(self, service):
        path = service.get('url')
        if not path.startswith('/'):
            path = '/' + path
        url = 'http://' + self.target.get('host') + path
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': random.choice(USER_AGENTS)}) as resp:
                status = str(resp.status)
        if not status.startswith('4') and not status.startswith('5'):
            self.alive_services.append(service.get('id'))
