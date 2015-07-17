ctf-pwn
=======

**Note**: This is (still) old code, which partially sucks. But it should provide a brief understanding on what may be done. There is a lot of room for improvements.


A simple offensive framework for attack/defense CTFs. It takes care of running exploits and flag submission. Mainly for preventing loss of flags due to unreachable gameservers.

## flag-submitter

### service
Listening on a TCP socket, takes flags and stores them in a (MariaDB/MySQL) database. Submits new flags and retrys if the gameserver is down. Takes one or more flags in the following format:

```    
SERVICE|TARGET|FLAG
```

The flag-submitter service runs on TCP port ```8000```

### frontend
Tiny Flask application which provides a JSON based REST API via HTTP. It just reads some stats from the database and returns them in a JSON object. Currently only the base path returns some data. Someone should write some fancy statistic function. The frontend listens on TCP port ```8001```.

Get (nearly) live simple stats:
    
**watch -n1 curl -s http://localhost:8001/**

### Deyploment
First, run **init.sh** to initialize the setup and do some dependency checking.

Use **requirements.txt** to deploy a virtualenv:
    
```
virtualenv env
env/bin/pip install -r requirements.txt
```

Run service and frontend:
    
```
env/bin/python run-service.py
```

Note: The service should run in a separate shell because it prints ANSI color output to STDOUT. ```aterm``` proofed to handle massive STDOUT output pretty good.

```
env/bin/python run-frontend.py
```

## exploit
The **parallel.sh** script is a simple wrapper for GNU parallel. It runs simple exploit scripts in parallel.
    
**./parallel.sh targets.txt exploit.py**

* **targets.txt**: Should be a file with IP addresses, one per line.
* **exploit.py**: An exploit script which takes one argument, an IP address, and outputs one or more flag/s in flag-submitter-friendly output. Can be any kind of executable (binaries, shell/python/ruby/perl/etc scripts).
