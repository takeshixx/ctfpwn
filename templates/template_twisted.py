#!/usr/bin/env python3
import sys
import re
from twisted.internet import task, defer, protocol

DEBUG = True

if len(sys.argv) is not 3:
    print('usage: {} [ip] [port]'.format(sys.argv[0]))
    sys.exit(1)

target_ip = sys.argv[1]
try:
    target_port = int(sys.argv[2])
except ValueError:
    print('Invalid port number: {}'.format(sys.argv[2]))
    sys.exit(1)

# Global instance to grep for flags, e.g.JAJAJAJAJAJAJAJAJAJAJAJAJAJAJAA=
FLAG_GREP = re.compile(br"(\w{31}=)")


class Exploit(protocol.Protocol):
    """This is where the protocol has to be implemented."""
    def connectionMade(self):
        """At this point to the server has been established. It is a
        good time to start sending initial stuff to the server.

        In order to do so, you could .e.g.

        self.writeLine('Hello, this is john')"""

    def dataReceived(self, data):
        if DEBUG:
            print('received: {}'.format(data))

    def writeLine(self, data):
        if hasattr(data, 'encode'):
            data = data.encode('utf-8')
        self.transport.write(data)
        self.transport.write(b'\n')

    def connectionLost(self, reason):
        pass


class ExploitFactory(protocol.ClientFactory):
    """This class is more or less just a Twisted formality. Changing
    it is most likely not required."""
    def __init__(self):
        self.done = defer.Deferred()

    def buildProtocol(self, addr):
        return Exploit()

    def startedConnecting(self, connector):
        pass

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        self.done.callback(None)

    def clientConnectionFailed(self, connector, reason):
        if DEBUG:
            print('Connection failed: {}'.format(reason))
        self.done.errback(reason)


def main(reactor):
    factory = ExploitFactory()
    reactor.connectTCP(target_ip, target_port, factory)
    return factory.done

if __name__ == '__main__':
    task.react(main)
