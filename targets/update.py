#!/usr/bin/env python2
import sys
from pymongo import MongoClient

if __name__ == '__main__':
    try:
        client = MongoClient()
        db = client.exploitservice
        col = db.targets
        f = open('/srv/targets/alive')
    except Exception as e:
        print(e)
        sys.exit(1)

    hosts = set(e['host'].encode() for e in col.find())
    for target in f:
        target = target.strip()
        col.update_one(
            {'host': target},
            {
                '$set': {
                    'alive': True
                }
            }
        )
        if target in hosts:
            hosts.remove(target)

    print("#Hosts remaining: %d" % len(hosts))
    for h in hosts:
        col.update_one(
            {'host': target},
            {
                '$set': {
                    'alive': False
                }
            }
        )

    print('Targets updated')