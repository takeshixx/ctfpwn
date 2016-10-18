#!/usr/bin/env python
"""This is an exploit template which includes some functions that should
make the process of writing exploits quicker and easier."""
import sys
import re
import socket
import time
import md5

# Recommended for HTTP related tasks
# Docs: http://docs.python-requests.org/en/latest/
import requests

if sys.version_info > (3,0,0):
    xrange = range

if len(sys.argv) is not 3:
    print('Usage: {} [ip] [port]'.format(sys.argv[0]))


def get_by_http(url):
    response = requests.get(url)
    return response.text

def exploit(targetIP, targetPort):
    diff = 20
    for i in range(diff):
        _id = md5.new()
	_id.update(int(time.time())


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
