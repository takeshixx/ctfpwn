#!/usr/bin/env python
"""This is an exploit template which includes some functions that should
make the process of writing exploits quicker and easier."""
import sys
import re
import socket

# Recommended for HTTP related tasks
# Docs: http://docs.python-requests.org/en/latest/
import requests


def get_something_via_http():
    response = requests.get('http://example.org/abc')
    print(response.text)


def recv_end(the_socket, end=']'):
    """This function reads from a socket until it hits whats defined in end."""
    total_data=[];data=''
    while True:
            data=the_socket.recv(8192)
            if end in data:
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


def exploit():
    # Do all the exploitation stuff here, return a list of flags
    pass


def main():
    try:
        flags = exploit()

        # The exploit only needs to print the flags, one per line.
        for flag in flags:
            print(flag)

        return 0
    except Exception as e:
        print(e)
        return 1

if __name__ == '__main__':
    sys.exit(main())