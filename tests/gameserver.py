#!/usr/bin/env python2
"""A simple gameserver that returns random states for submitted flags."""
import sys
import socket
import re
from random import choice
from thread import *
states = ['expired','no such flag','accepted', 'corresponding', 'own flag']
flag_grep = re.compile(r"(\w{31}=)")

def clientthread(conn, addr):
    conn.send('Welcome to the gameserver and stuff\n')
    print('New connection from {}'.format(addr[0]))
    flags = []
    while True:
        try:
            data = conn.recv(1024)
            flags += flag_grep.findall(data)
            resp = choice(states)
            conn.send(resp+'\n')
        except Exception as e:
            print('Received {} flags'.format(len(flags)))
            conn.close()
            return

while True:
    try:
        sock = socket.socket()
        sock.bind(('127.0.0.1', 9000))
        sock.listen(10)
        while True:
            conn, addr = sock.accept()
            start_new_thread(clientthread,(conn, addr))
    except KeyboardInterrupt:
        sock.close()
        sys.exit(0)
    except Exception as e:
        print(str(e))
