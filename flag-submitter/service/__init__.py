import re
import datetime
from time import *
from sys import exit
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.internet import reactor, protocol
from sqlalchemy import *

from utils.tinylogs import TinyLogs
from utils.flagdb import FlagDB
from utils.gameserver import Gameserver


# Local flag-service settings
SERVICE_PORT = 8000
SERVICE_INTERFACE = '127.0.0.1'
SERVICE_SUBMIT_INTERVAL = 5 # seconds
SERVICE_STATS_INTERVAL = 60 # seconds

# Gameserver settings
GAMESERVER_ADDR = '127.0.0.1'
GAMESERVER_PORT = 9000
GAMESERVER_TIMEOUT = 2
GAMESERVER_CHUNK_SIZE = 10

# Flag regex
# Input format example: 'smartgrid|10.23.103.2|128ecf542a35ac5270a87dc74091840'
REGEX_FLAG = r"(\w{31})"
REGEX_SERVICE = r"(\w+)"
REGEX_IP = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
REGEX_INPUT = '^{}\|{}\|{}$'.format(REGEX_SERVICE,REGEX_IP,REGEX_FLAG)

log = TinyLogs()
input_validation = re.compile(REGEX_INPUT)


class Flag():
    """
    A class that represents flags, as parsed from incoming lines. See REGEX_INPUT
    and the corresponding input format example.
    """
    def __init__(self,incoming):
        self.service = incoming[0]
        self.target = incoming[1]
        self.flag = incoming[2]


class FlagSubmitProtocol(protocol.Protocol):
    """
    Protocol factory for flag submission.
    """
    def __init__(self):
        self.buff = []


    def dataReceived(self, incoming):
        """
        Instance function that actually handles incoming data. If lines math
        REGEX_INPUT, it will be inserted into the database.
        """
        try:
            lines = incoming.split('\n')
            for line in lines:
                line = line.strip()
                if input_validation.findall(line):
                    flag = Flag(line.strip().split('|'))
                    db = FlagDB()
                    db.insertNew(flag)
                else:
                    self.transport.write('bogus format!\n')
        except Exception as e:
            log.warning('Error in dataReceive() function! [EXCEPTION: {}'.format(e))


def printStats():
    """
    This function will be called by the protocol factory every SERVICE_STATS_INTERVAL seconds.
    It just prints some stats to STDOUT.
    """
    db = FlagDB()
    stats = db.databaseStats()
    if len(stats)<6:
        return
    time_latest = datetime.datetime.fromtimestamp(int(stats['latest_submitted_timestamp'])).strftime('%H:%M:%S')

    log.stats('[\033[93mFLAGS\033[0m] [\033[93mTOTAL\033[0m \033[1;1m{}\033[0m] [\033[93mSUBMITTED\033[0m \033[1;1m{}\033[0m] [\033[93mEXPIRED\033[0m \033[1;1m{}\033[0m] [\033[93mFAILED\033[0m \033[1;1m{}\033[0m]\n'.format(
            stats['total_count'],stats['submitted_count'],stats['expired_count'],stats['failed_count']))
    log.stats('[\033[93mLATEST CAPTURE\033[0m] [\033[93mSERVICE\033[0m \033[1;1m{}\033[0m] [\033[93mTIME\033[0m \033[1;1m{}\033[0m]\n'.format(stats['latest_submitted_service'],time_latest))


def submitPending():
    """
    This function will be called by the protocol factory every SERVIE_RESUBMIT_INTERVAL seconds.
    It takes all flags with status New and Pending from the database and trys to submit them
    to the gameserver.
    """
    try:
        db = FlagDB()
        rows = db.selectNewPending()

        if rows:
            chunks = map(None, *([iter(rows)] * GAMESERVER_CHUNK_SIZE))
            log.debug('Starting {} submission threads ({} flags per thread)'.format(len(chunks),GAMESERVER_CHUNK_SIZE))
            for chunk in chunks:
                gameserver = Gameserver()
                t0 = time()
                deferToThread(gameserver.submit,chunk)
                t1 = time() - t0
                log.debug('gameserver.submit() took {}'.format(t1))
        else:
            log.stats('No NEW/PENDING flags found in database...')

    except KeyboardInterrupt:
        exit(0)
    except Exception as e:
        log.warning('Error in submitPending() function! [EXCEPTION {}]'.format(e))
    

def run_service():
    """
    Main function which handles requests and application logic. This function needs to be called
    in order to start the flag-service.
    """
    try:
        factory = protocol.ServerFactory()
        factory.protocol = FlagSubmitProtocol
        reactor.listenTCP(SERVICE_PORT,factory,interface=SERVICE_INTERFACE)

        # Try submitting NEW and PENDING flags every SERVIE_RESUBMIT_INTERVAL seconds
        submit = LoopingCall(submitPending)
        submit.start(SERVICE_SUBMIT_INTERVAL)

        # Print stats every SERVICE_STATS_INTERVAL seconds
        stats = LoopingCall(printStats)
        stats.start(SERVICE_STATS_INTERVAL)

        reactor.run()
    except KeyboardInterrupt:
        exit(0)
    except Exception as e:
        log.warning('Error in main() function! [EXCEPTION {}]'.format(e))        
