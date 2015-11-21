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

    col.update({}, {'$set': {'alive': False}}, multi=True)

    for target in f.readline():
        col.update_one(
            {'host': target},
            {
                '$set': {
                    'alive': True
                }
            }
        )

    print('Targets updated')

