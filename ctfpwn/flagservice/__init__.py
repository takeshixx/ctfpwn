#!/usr/bin/env python3
import sys
import asyncio
import logging

from helperlib.logging import default_config, load_config

from ctfpwn.db import CtfDb
from ctfpwn.shared import load_ctf_config
from ctfpwn.flagservice.receiver import FlagReceiverProtocol
from ctfpwn.flagservice.supervisor import FlagSupervisor

log = logging.getLogger(__name__)


async def stats(db, config):
    while True:
        await db.flag_stats()
        await asyncio.sleep(config.get('flag_stats_interval'))


async def _start(loop, config):
    db = await CtfDb.create(config=config)
    loop.create_task(stats(db, config))
    supervisor = FlagSupervisor(db, config)
    supervisor.start()
    receiver = loop.create_server(lambda: FlagReceiverProtocol(db),
                                  config.get('flag_service_host'),
                                  config.get('flag_service_port'))
    loop.create_task(receiver)


def run_flagservice(config=None):
    """Main function which handles requests and application
    logic. This function needs to be called in order to start
    the flag-service."""
    try:
        load_config('flagservice.ini', disable_existing_loggers=False)
    except Exception as e:
        default_config(level=logging.DEBUG, disable_existing_loggers=False)
        log.warning('No logging config file flagservice.ini found. Using default')

    config = load_ctf_config(config)
    log.info('Starting Flag Service')
    loop = asyncio.get_event_loop()
    loop.create_task(_start(loop, config))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        tasks = asyncio.Task.all_tasks()
        log.warning("Caught keyboard interrupt. Canceling %d tasks...", len(tasks))
        tasks = asyncio.gather(*tasks)
        tasks.cancel()
        loop.stop()
        loop.run_forever()
    except Exception as e:
        print(e)
        sys.exit(1)
    finally:
        loop.close()


if __name__ == '__main__':
    run_flagservice()
