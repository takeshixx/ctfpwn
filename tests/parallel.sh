#!/bin/sh

DEBUG=1

# Change this
readonly FLAG_SERVICE_ADDR="127.0.0.1"
readonly FLAG_SERVICE_PORT=8081

# Probably change this
readonly GNUP_DELAY=0
readonly GNUP_TIMEOUT=18
readonly GNUP_MAXPROCS=8 # Adjust to count of CPUs
readonly ITER_SLEEP=45

# Do not change this
declare COUNT=1
readonly targets="$1"
readonly exploiter="$2"
readonly service="$2"
declare -a TARGETS
declare EXPLOITER

usage (){
	echo -e "parallel.sh targets exploiter service"
	echo
	echo -e "targets: \tIPs, one per line."
	echo -e "exploiter: \tA script that's executable. Should take an IP,\n\t\tand print flag-service compatible string."
    echo -e "service: \tThe name of the service."
	echo
}

err(){
    exitval=$1
    shift
    echo 1>&2 "[ERROR] $*"
    exit "$exitval"
}

warn(){
    echo -e "[WARNING] $*"
}

info(){
    echo -e "[INFO] $*"
}

debug(){
    case $DEBUG in
    [Yy][Ee][Ss]|[Tt][Rr][Uu][Ee]|[Oo][Nn]|1)
        echo -e "[DEBUG] $*"
        ;;
    esac
}

checkyesno(){
    if [ -z "$1" ];then
        return 1
    fi
    eval _value=\$${1}
    debug "checkyesno: $1 is set to $_value."
    case $_value in
        #   "yes", "true", "on", or "1"
    [Yy][Ee][Ss]|[Tt][Rr][Uu][Ee]|[Oo][Nn]|1)
        return 0
        ;;
        #   "no", "false", "off", or "0"
    [Nn][Oo]|[Ff][Aa][Ll][Ss][Ee]|[Oo][Ff][Ff]|0)
        return 1
        ;;
    *)
        return 1
        ;;
    esac
}

check_dependencies (){
	if ! which parallel;then
		err 1 "GNU parallel is required!"
	fi
}

check_args (){
    if [[ -z "$targets" || -z "$exploiter" || -z "$service" ]];then
		usage
		exit 1
	fi

    if [[ -e "$targets" && -e "$exploiter" ]];then
        TARGETS=$(cat "$targets")
    else
        usage
        exit 1
    fi
}

main (){
	check_dependencies
	check_args

	while :
	do
	    info "[RUN ${COUNT}]"

	    echo "$TARGETS" \
	    	| parallel \
		        --no-notice \
		        --delay "$GNUP_DELAY" \
		        --timeout "$GNUP_TIMEOUT" \
		        --max-procs="$GNUP_MAXPROCS" \
		        -u \
                "$exploiter" \
                {} \
		        | tee /dev/stderr |ncat "$FLAG_SERVICE_ADDR" "$FLAG_SERVICE_PORT" 

	    info "[SLEEP ${SLEEP}]"
	    sleep "$ITER_SLEEP"
        COUNT=$(($COUNT+1))
	done
}

main
