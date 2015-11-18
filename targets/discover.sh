#!/bin/sh

targets="10.60.1-41.2 10.60.43-254.2 10.61.1-234.2"

while :;do
    nmap -sP -PS22 -oG - "${targets}" | grep "Status: Up" | awk '{print $2}' > /srv/targets/alive
    /srv/targets/update.py
    sleep 10;
done
