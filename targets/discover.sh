#!/bin/sh
# This script checks which hosts in the CTF range are up.
# It writes all alive IPs into /srv/targets/alive and calls
# /srv/ctf-pwn/targets/update.py which updates the status
# of the alive hosts in the database.
#
# This script will be started manually via Supervisor.

# TODO: Add the ports of all services to the Nmap port list
# in order to make more reliable alive checks.

targets="10.60.1-41.2 10.60.43-254.2 10.61.1-234.2"

while :;do
    nmap -sP -PS22,80 -oG - "${targets}" | grep "Status: Up" | awk '{print $2}' > /srv/targets/alive
    /srv/ctf-pwn/targets/update.py
    sleep 10;
done
