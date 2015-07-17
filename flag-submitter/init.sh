#!/bin/sh

readonly KERNEL=$(uname -s)

if [ "$KERNEL" = "Linux" ];then
    if [ -z "$(netstat -tulpn|grep 3306)" ];then
        echo "MySQL is not running on port 3306"
        exit 1
    fi
elif [ "$KERNEL" = "FreeBSD" ];then
    if [ -z "$(sockstat -4|grep 3306)" ];then
        echo "MySQL is not running on port 3306"
        exit 1
    fi
fi

if [ -z "$(which virutalenv)" ];then
    echo "virtualenv not found"
    exit 1
fi

if [ -z "$(which mysql)" ];then
    echo "mysql client not found"
    exit 1
fi

if [ ! -d "env" ];then
    virtualenv2 env
    env/bin/pip install -r requirements.txt
fi

if [ -z "$(which aterm)" ];then
    echo "aterm not found. flag-service should run within aterm."
fi