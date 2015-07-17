import flask
import datetime
from flask import Flask
from sqlalchemy import *


app = Flask(__name__)


@app.route("/")
def stats():
    db = DB()
    total = db.countAll()
    new = db.countNew()
    pending = db.countPending()
    accepted = db.countSubmitted()
    expired = db.countExpired()
    failed = db.countFailed()
    stats = {}
    stats['service stats'] = {}
    stats['flag stats'] = {'total':total,'accepted':accepted,'expired':expired,'new':new,'pending':pending,'failed':failed}
    services = db.getServices()
    for service in services:
        flags_total = db.countAll(service)
        flags_failed = db.countFailed(service)
        flags_expired = db.countExpired(service)
        flags_submitted = db.countSubmitted(service)
        flags_latest = db.getLatestSubmit(service)
        latest_time = datetime.datetime.fromtimestamp(int(flags_latest)).strftime('%H:%M:%S')
        service_stats = {'total':flags_total,'failed':flags_failed,'expired':flags_expired,'accepted':flags_submitted,'latest':latest_time}
        stats['service stats'][service] = service_stats

    return flask.jsonify(stats)


class DB():
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
            print str(e)


    def countAll(self,service=None):
        if service:
            sel = select([func.count()],self.flags.c.service==service).select_from(self.flags)
        else:
            sel = select([func.count()]).select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            return row[0]


    def countNew(self):
        sel = select([func.count()],self.flags.c.state=='NEW').select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            return row[0]


    def countPending(self):
        sel = select([func.count()],self.flags.c.state=='PENDING').select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            return row[0]


    def countSubmitted(self,service=None):
        if service:
            sel = select([func.count()],and_(self.flags.c.state=='SUBMITTED',self.flags.c.service==service))
        else:
            sel = select([func.count()],self.flags.c.state=='SUBMITTED').select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            return row[0]


    def countExpired(self,service=None):
        if service:
            sel = select([func.count()],and_(self.flags.c.state=='EXPIRED',self.flags.c.service==service)).select_from(self.flags)
        else:
            sel = select([func.count()],self.flags.c.state=='EXPIRED').select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            return row[0]


    def countFailed(self,service=None):
        if service:
            sel = select([func.count()],and_(self.flags.c.state=='FAILED',self.flags.c.service==service)).select_from(self.flags)
        else:
            sel = select([func.count()],self.flags.c.state=='FAILED').select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            return row[0]


    def getServices(self):
        sel = select([self.flags.c.service]).group_by(self.flags.c.service)
        result = self.conn.execute(sel)
        ret = []
        for row in result:
            ret.append(row[0])
        return ret


    def getLatestSubmit(self,service):
        if service:
            sel = select([self.flags.c.timestamp,],and_(self.flags.c.state=='SUBMITTED',self.flags.c.service==service)).order_by(self.flags.c.timestamp.desc()).limit(1)
        else:
            sel = select([func.count()],self.flags.c.state=='FAILED').select_from(self.flags)
        result = self.conn.execute(sel)
        for row in result:
            return row[0]
            

    def getServiceStats(self,service):
        sel = select([self.flags],self.flags.c.service==service)
        result = self.conn.execute(sel)
        for row in result:
            return row[0]

