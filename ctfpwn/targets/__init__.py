#!/usr/bin/env python3
import logging
import sys
import asyncio

from ctfpwn.db import CtfDb
from ctfpwn.shared import load_ctf_config
from ctfpwn.targets.supervisor import TargetSupervisor

log = logging.getLogger(__name__)


async def stats(db, config):
    while True:
        await db.targets_stats()
        await asyncio.sleep(config.get('target_stats_interval'))


async def _start(loop, config):
    db = await CtfDb.create(config=config)
    loop.create_task(stats(db, config))
    supervisor = TargetSupervisor(db, config)
    supervisor.start(config.get('discovery_interval'),
                     config.get('service_interval'))


def run_targetservice(config=None):
    config = load_ctf_config(config, logging_section='targetservice')
    log.info('Starting Target Service')
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
    run_targetservice()
