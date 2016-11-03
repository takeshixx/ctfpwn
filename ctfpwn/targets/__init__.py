#!/usr/bin/env python3
import logging
import sys
import asyncio

from helperlib.logging import default_config, load_config

from ctfpwn.db import CtfDb
from ctfpwn.shared import load_ctf_config
from ctfpwn.targets.supervisor import TargetSupervisor

log = logging.getLogger(__name__)

# TODO: move to configuration file
DISCOVERY_INTERVAL = 45
SERVICE_INTERVAL = 15
# TODO: include open ports of vulenrable vm
DISCOVER_PORTS = [22, 80, 8080]
SERVICE_PORTS = [80, 9090]
CTF_NETWORK = '172.23.11.0/24'


async def _start(config):
    db = await CtfDb.create(config=config)
    supervisor = TargetSupervisor(db,
                                  networks=config.get('ctf_network'),
                                  discover_ports=config.get('discovery_ports'),
                                  service_ports=config.get('service_ports'))
    supervisor.start(config.get('discovery_interval'), config.get('service_interval'))


def run_targetservice(config='config.yaml'):
    try:
        load_config('targetservice.ini', disable_existing_loggers=False)
    except Exception as e:
        default_config(level=logging.DEBUG, disable_existing_loggers=False)
        log.warning('No logging config file targetservice.ini found. Using default')

    config = load_ctf_config(config)
    log.info('Starting Target Service')
    loop = asyncio.get_event_loop()
    loop.create_task(_start(config))
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
    run_targetservice()
