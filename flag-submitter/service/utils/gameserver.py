"""Utils for remote gameserver communications."""

import socket
from time import *
from tinylogs import TinyLogs
from flagdb import FlagDB


# Gameserver settings
GAMESERVER_ADDR = 'localhost' # Address of the gameserver
GAMESERVER_PORT = 8002 # Port of the gameserver
GAMESERVER_TIMEOUT = 2

log = TinyLogs()


class Gameserver():
    """
    This class handles any communication with the gameserver. It needs to be adjusted
    to the corresponding gameserver protocol to be able to determin if submissions
    are successful, or submission failed, or flags are invalid.
    """
    def __init__(self):
        self.flags_success = []
        self.flags_failed = {}
        self.flags_expired = []
        self.flags_pending = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(GAMESERVER_TIMEOUT)
        self.socket.connect((GAMESERVER_ADDR, GAMESERVER_PORT))


    def submit(self,rows):
        """
        General submission function which takes one or more flags and trys to submit them.
        """
        log.debug('Submitting \033[1;1m{}\033[0m NEW/PENDING flags'.format(len(rows)))
        try:
            for row in rows:
                if row is None:
                    continue
                service = row[0]
                target = row[1]
                flag = row[2]
                comment = row[3]
                self.socket.send('{}\n'.format(flag))
                resp = self.socket.recv(1024)

                if 'accepted' in resp:
                    log.info('\033[1;1m[\033[0m\033[96m{}\033[0m\033[1;1m]\033[0m [{}] [{}]'.format(service,flag,target))
                    self.flags_success.append(flag)
                    continue

                if 'expired' in resp:
                    log.debug('Flag expired')
                    self.flags_expired.append(flag)
                    continue

                if 'corresponding' in resp:
                    log.warning('\033[1;1m[\033[0m\033[96m{}\033[0m\033[1;1m]\033[0m SERVICE IS DOWN!'.format(service))
                    self.flags_pending.append(flag)
                    continue

                if 'no such flag' in resp:
                    log.debug('\033[1;1m[\033[0m\033[96m{}\033[0m\033[1;1m]\033[0m NOT A VALID FLAG [{}] [{}] [{}]'.format(service,flag,target,comment))
                    self.flags_failed[flag] = resp
                    continue

                if 'own flag' in resp:
                    self.flags_failed[flag] = resp
                    continue

            self.socket.close()
            self._updateFlagStatus()
        except Exception as e:
            log.warning('Error in submit() function! [EXCEPTION: {}]'.format(e))


    def _updateFlagStatus(self):
        """
        This function will always be called after flag submission in order to update
        the status of submitted flags.
        """
        t0 = clock()
        log.stats('[\033[93mSUBMIT\033[0m] [\033[32mACCEPTED\033[0m \033[1;1m{}\033[0m] [\033[93mPENDING\033[0m \033[1;1m{}\033[0m] [\033[31mEXPIRED\033[0m \033[1;1m{}\033[0m] [\033[93mUNKNOWN\033[0m \033[1;1m{}\033[0m]'.format(len(self.flags_success),len(self.flags_pending),len(self.flags_expired),len(self.flags_failed)))
        db = FlagDB()
        if self.flags_success:
            for flag in self.flags_success:
                db.updateSubmitted(flag)
        
        if self.flags_expired:
            for flag in self.flags_expired:
                db.updateExpired(flag)
        
        if self.flags_pending:
            for flag in self.flags_pending:
                db.updatePending(flag)

        if self.flags_failed:
            for flag in self.flags_failed:
                db.updateFailed(flag,self.flags_failed[flag])
        t1 = clock() - t0
        log.stats('_updateFlagStatus() took {}'.format(t1))
