#!/usr/bin/env python3
import logging
import sys
import asyncio
import signal

from helperlib.logging import default_config, load_config

#from ctfpwn.exploitservice.exploitdb import ExploitDB
from ctfpwn.db import CtfDb
from ctfpwn.targets.supervisor import TargetSupervisor

log = logging.getLogger(__name__)

# TODO: move to configuration file
DISCOVERY_INTERVAL = 45
SERVICE_INTERVAL = 15
# TODO: include open ports of vulenrable vm
DISCOVER_PORTS = [22, 80, 8080]
SERVICE_PORTS = [80, 9090]
CTF_NETWORK = '172.23.11.0/24'


async def _start():
    db = await CtfDb.create()
    supervisor = TargetSupervisor(db,
                                  networks=CTF_NETWORK,
                                  discover_ports=DISCOVER_PORTS,
                                  service_ports=SERVICE_PORTS)
    supervisor.start(DISCOVERY_INTERVAL, SERVICE_INTERVAL)

def run_targetservice():
    try:
        load_config('targetservice.ini', disable_existing_loggers=False)
    except Exception as e:
        default_config(level=logging.DEBUG, disable_existing_loggers=False)
        log.warning('No logging config file targetservice.ini found. Using default')

    log.info('Starting Target Service')
    loop = asyncio.get_event_loop()
    loop.create_task(_start())
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
    run_targetservice()
