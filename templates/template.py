#!/usr/bin/env python
"""This is an exploit template which includes some functions that should
make the process of writing exploits quicker and easier."""
import sys
import re
import socket

# Recommended for HTTP related tasks
# Docs: http://docs.python-requests.org/en/latest/
import requests

if sys.version_info > (3,0,0):
    xrange = range

def get_by_http(url):
    response = requests.get(url)
    return response.text


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


def exploit(targetIP, targetPort):
    # Do all the exploitation stuff here, return a list of flags
    pass


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
