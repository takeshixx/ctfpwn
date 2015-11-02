#!/bin/sh

readonly KERNEL=$(uname -s)

if [ "$KERNEL" = "Linux" ];then
    if [ -z "$(netstat -tulpn|grep 27017)" ];then
        echo "MongoDB is not running on port 27017"
        exit 1
    fi
elif [ "$KERNEL" = "FreeBSD" ];then
    if [ -z "$(sockstat -4|grep 27017)" ];then
        echo "MongoDB is not running on port 27017"
        exit 1
    fi
fi

if [ -z "$(which virutalenv2)" ];the
    echo "virtualenv not found"
    exit 1
fi

if [ ! -d "env" ];then
    virtualenv2 env
    env/bin/pip install -r requirements.txt
fi

if [ -z "$(which aterm)" ];then
    echo "aterm not found. flag-service should run within aterm."
fi
