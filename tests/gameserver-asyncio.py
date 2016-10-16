#!/usr/bin/env python3.5
"""A simple gameserver based on asyncio that returns
random states for submitted flags.

./gameserver-asyncio.py [host] [port]"""
import sys
import socket
import re
import asyncio
import random
import codecs

HOST = '127.0.0.1'
PORT = 8888
STATES = [b'expired', b'no such flag', b'accepted', b'corresponding', b'own flag']
FLAGS = re.compile(br'(\w{31}=)')


class GameServerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        self.peername = transport.get_extra_info('peername')
        self._write_line(b'Welcome to the Game Server, send me flags...')

    def data_received(self, data):
        response = b''
        for line in data.split(b'\n'):
            if not line:
                continue
            if not FLAGS.findall(line):
                self._write_line(b'invalid flag')
                continue
            response += random.choice(STATES)
            response += b'\n'
        self.transport.write(response)

    def _write_line(self, data):
        if isinstance(data, str):
            data = codecs.encode(data)
        self.transport.write(data + b'\n')


if __name__ == '__main__':
    print('Starting Game Server')
    if len(sys.argv) >= 2:
        HOST = sys.argv[1]
        try:
            socket.inet_aton(HOST)
        except socket.error:
            print('Invalid IP address')
            sys.exit(1)
        if len(sys.argv) == 3:
            PORT = sys.argv[2]
            try:
                int(PORT)
            except ValueError:
                print('Port is not an int')
                sys.exit(1)
    loop = asyncio.get_event_loop()
    c = loop.create_server(GameServerProtocol, HOST, PORT)
    server = loop.run_until_complete(c)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
