ctf-pwn
=======

A simple offensive framework for attack/defense CTFs. It takes care of running exploits and handles periodic flag submission. Mainly for preventing loss of flags due to unreachable gameservers.

It is split into two major parts: the `exploitservice` and `flagservice`, each is a separate Twisted application. They share a single MongoDB instance.

**TODO**:

* Add info of new structure to `README.md`.
* Implement a way to update a list of proper targets.
** Just pings?
** Portscans? With Twisted or maybe Nmap?
* Implement periodic checks of own services.

# exploitservice

This service is responsible for the execution of exploits.

## Exploits

An exploit is supposed to be an executable file, which takes two arguments:

1. Target IP address
2. Port number

Exploits are supposed to print one or more flags, nothing else. Exploits should reside in an own directory under `/srv/exploits`.

## Schedule exploits for execution

In order to schedule exploits, the have to be added to the exploits collection. A new exploit can be added to the database as follows:

```
db.exploits.insert({
    "exploit" :     "/srv/exploits/crasher/unstable_exploit.py",
    "port" :        8081,
    "service" :     "crasher",
    "enabled" :     true
})
```

The exploitservice contains a simple wrapper script called `client.py` which can be used to add exploits from the command line:

```
cd /srv/ctf-pwn/exploitservice
../env/bin/python client.py crasher /srv/exploits/crasher/unstable_exploit.py 8081 false
```

Executing the same command with `true` instead of `false` will enable the exploit:

```
cd /srv/ctf-pwn/exploitservice
../env/bin/python client.py crasher /srv/exploits/crasher/unstable_exploit.py 8081 true
```

*Note*: Currently `client.py` must be executed exactly like this, with an absolute path. It is also mandatory to executed it from within the exploitservice directory because it relies on the `exploitdb.py` module.



# flagservice

The flagservice periodically queries flags from the `flags` collection and tries to submit them to the gameserver.

## TCP/IP interface

In case the exploitservice fails, flagservice provides a fallback interface which allows to submit flags on the local network via a telnet-like service running on TCP port `8081`.

Submission format looks as follows:

```
SERVICE|TARGET|FLAG|TIMESTAMP
```

Here is an example:

```
smartgrid|10.23.103.2|JAJAJAJAJAJAJAJAJAJAJAJAJAJAJAA=|1446295211
```

# Monitoring the services

Both services log to the `/srv/logs/{exploitservice,flagservice}` directories. Each contains a `stdout.log` and `stderr.log` file.

It is recommended to monitor both streams in different shells as follows:

## stdout

```
tail -f {exploitservice,flagservice}/stdout.log |ccze
```

## stderr

```
tail -f {exploitservice,flagservice}/stderr.log |ccze
```

*Note*: It is not recommended to log bot `stdout.log` and `stderr.log` to the same shell as it might result in a flood of messages.

# Manage services

Both services are managed via Supervisor. They can be started via `supervisorctl`, e.g.:

```
# supervisorctl
supervisor> restart exploitservice
```

or via a web interface running on TCP port `9001`.