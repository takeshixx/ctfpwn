#!/usr/bin/env python2
import sys
import string
import random
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

if len(sys.argv)>=2:
    ADDR = sys.argv[1]
    PORT = int(sys.argv[2])
else:
    ADDR = '127.0.0.1'
    PORT = 9000

def generate_flag():
    flag = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(31))
    flag += '='
    return flag

class ServiceProtocol(Protocol):

    def connectionMade(self):
        print('Got a connection...')
	self.writeLn('Weclome to service1')
	self.writeLn('Please send me some magic data...')

    def dataReceived(self, data):
	self.writeLn('Here is your flag:')
        self.writeLn(generate_flag())
        self.transport.loseConnection()
        return

    def writeLn(self, msg):
	self.transport.write('{}\n'.format(msg))
	

def main():
    print('Starting service on {}:{}'.format(ADDR, PORT))
    f = Factory()
    f.protocol = ServiceProtocol
    reactor.listenTCP(PORT, f, interface=ADDR)
    reactor.run()

if __name__ == '__main__':
    main()
