"""Utils for local database communications."""

from time import *
from sqlalchemy import *
from tinylogs import TinyLogs


log = TinyLogs()


class FlagDB():
    def __init__(self):
        try:
            self.db = create_engine('mysql://flagservice:6_-fKSAJz3dz?>Z]@127.0.0.1')
            self.db.execute('USE flagservice')
            metadata = MetaData()
            self.flags = Table('flags', metadata,\
                    Column('fid',Integer, primary_key = True),
                    Column('service',String(50)),
                    Column('target',String(50)),
                    Column('flag',String(50)),
                    Column('state',String(50)),
                    Column('comment',String(100)),
                    Column('timestamp',String(50)))

            self.conn = self.db.connect()

        except Exception as e:
            log.warning('Error in DB() initialization! [EXCEPTION {}]'.format(e))


    def selectNewPending(self):
        sel = select([self.flags.c.service,self.flags.c.target,self.flags.c.flag,
                self.flags.c.comment],or_(self.flags.c.state=='NEW',self.flags.c.state=='PENDING')).limit(50) 
        result = self.conn.execute(sel)
        flags = []
        for row in result:
            flags.append(row)
        return flags


    def insertNew(self,flag):
        sel = select([self.flags.c.flag],self.flags.c.flag==flag.flag)
        result = self.conn.execute(sel)
        for row in result:
            return
        ins = self.flags.insert().values(service=flag.service,target=flag.target, \
            flag=flag.flag,state='NEW',comment='',timestamp=int(time()))

        result = self.conn.execute(ins)


    def updateSubmitted(self,flag):
        up = self.flags.update().where(self.flags.c.flag==flag).values(state='SUBMITTED')
        self.conn.execute(up)


    def updatePending(self,flag):
        up = self.flags.update().where(self.flags.c.flag==flag).values(state='PENDING')
        self.conn.execute(up)


    def updateExpired(self,flag):
        up = self.flags.update().where(self.flags.c.flag==flag).values(state='EXPIRED')
        self.conn.execute(up)


    def updateFailed(self,flag,comment=''):
        up = self.flags.update().where(self.flags.c.flag==flag).values(state='FAILED',comment=comment)
        self.conn.execute(up)


    def databaseStats(self):
        stats = {}
        sel = select([func.count()]).select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            stats['total_count'] = row[0]

        sel = select([func.count()],self.flags.c.state=='SUBMITTED').select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            stats['submitted_count'] = row[0]

        sel = select([func.count()],self.flags.c.state=='EXPIRED').select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            stats['expired_count'] = row[0]

        sel = select([func.count()],self.flags.c.state=='FAILED').select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            stats['failed_count'] = row[0]

        sel = select([func.max(self.flags.c.timestamp)],self.flags.c.state=='SUBMITTED').select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            stats['latest_submitted_timestamp'] = row[0]

        sel = select([self.flags.c.service],self.flags.c.timestamp==stats['latest_submitted_timestamp']).select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            stats['latest_submitted_service'] = row[0]

        return stats 
