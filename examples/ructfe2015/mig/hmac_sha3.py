#!/usr/bin/env python2
# coding: utf-8
from ctypes import *
libsha3 = CDLL('/srv/exploits/mig/libsha3.so')


def sha3(msg):
    buf = create_string_buffer(64)
    libsha3.rhash_sha3(32*8, msg, len(msg), buf)
    return buf.value


def hmac_sha3(key, data):
    if len(key) > 32:
        key = sha3(key)
    elif len(key) < 32:
        # ?? strange code?
        pass
    okey = []
    ikey = []
    for k in key:
        okey.append(ord(k) ^ 0x5c)
        ikey.append(ord(k) ^ 0x36)

    #ipart = []
    #for i, d in zip(ikey, data):
    #    ipart.append(i & ord(d))
    d = sha3(''.join(chr(d) for d in ikey) + data)

    #opart = []
    #for o, x in zip(okey, d):
    #    opart.append(o & ord(x))
    return sha3(''.join(chr(d) for d in okey) + d).encode('hex')


def get_hmac(login):
    key = 'fc90d26f7435c9fadb6cbcb1ca4e0f64af5eb4fe99705d180c4742602a8cc835'.decode('hex')
    return hmac_sha3(key, login)


if __name__ == '__main__':
    import sys
    print(get_hmac(sys.argv[1]))
#    expected = '89fbb3ec8c6dd895c7e1a8e57b9b3df7d70c317e9a6ee76957479dee8a935535'
#    key = 'fc90d26f7435c9fadb6cbcb1ca4e0f64af5eb4fe99705d180c4742602a8cc835'.decode('hex')
#    print(len(key))
#    msg = 'ldexcogic'
#
#    mac = hmac_sha3(key, msg)
#    print(mac)
#    print(mac == expected)
