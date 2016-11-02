#!/usr/bin/env python3
import sys
import asyncio
import logging

from helperlib.logging import default_config, load_config

from ctfpwn.db import CtfDb
from ctfpwn.flagservice.receiver import FlagReceiverProtocol
from ctfpwn.flagservice.submitter import submitter

log = logging.getLogger(__name__)

# TODO: move to config file
# Local flag-service settings
SERVICE_PORT = 8081
SERVICE_ADDR = '127.0.0.1'
# Interval settings for all jobs
SERVICE_SUBMIT_INTERVAL = 12
SERVICE_STATS_INTERVAL = 5
# According to rules, a round is about ~2 min, this corresponds
# to the validity times of flags. But this may vary.
CTF_ROUND_DURATION = 120


async def stats(db):
    while True:
        await db.flag_stats()
        await asyncio.sleep(SERVICE_STATS_INTERVAL)

async def init(loop):
    db = await CtfDb.create()
    # Print stats every SERVICE_STATS_INTERVAL seconds.
    loop.create_task(stats(db))
    loop.create_task(submitter(db, loop))
    receiver = loop.create_server(lambda: FlagReceiverProtocol(db), SERVICE_ADDR, SERVICE_PORT)
    loop.create_task(receiver)

def run_flagservice():
    """Main function which handles requests and application
    logic. This function needs to be called in order to start
    the flag-service."""
    try:
        load_config('flagservice.ini', disable_existing_loggers=False)
    except Exception as e:
        default_config(level=logging.DEBUG, disable_existing_loggers=False)
        log.warning('No logging config file flagservice.ini found. Using default')

    log.info('Starting Flag Service')
    loop = asyncio.get_event_loop()
    loop.create_task(init(loop))
    # loop.add_signal_handler(signal.SIGINT, loop.stop)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        tasks = asyncio.Task.all_tasks()
        log.warning("Caught keyboard interrupt. Canceling %d tasks...", len(tasks))
        tasks = asyncio.gather(*tasks)
        tasks.cancel()
        loop.stop()
        loop.run_forever()
        # tasks.exception()
    except Exception as e:
        print(e)
        sys.exit(1)
    finally:
        loop.close()


if __name__ == '__main__':
    run_flagservice()
