#!/usr/bin/env python2
import socket
from random import choice
from thread import *
#states = ['expired','no such flag','accepted','corresponding service down']
states = ['expired','no such flag','accepted', 'corresponding', 'own flag']


def clientthread(conn):
    conn.send('Welcome to the gameserver and stuff\n')
    while True:
        try:
            data = conn.recv(1024)
            print data
            resp = choice(states)
            conn.send(resp+'\n')
        except Exception as e:
            print str(e)
            conn.close()
            return

while True:
    try:
        sock = socket.socket()
        sock.bind(('127.0.0.1', 9000))
        sock.listen(10)
        while True:
            conn, addr = sock.accept()
            start_new_thread(clientthread,(conn,))
        conn.close()
        sock.close()
    except Exception as e:
        print str(e)
