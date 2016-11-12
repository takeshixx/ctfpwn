# EXAMPLE
# . ./ctfpwn_lib.sh
#
# parse_cmdline
#
# echo $IP
#
# set_http_base http://www.ernw.de
# http_head /
# foo="$(http_head / | dos2unix )"
# echo -e "$foo" | get_http_header Location

parse_cmdline() {
    if [[ ${#BASH_ARGV[@]} -lt 3 ]]
    then
        echo 'Invalid number of arguments. Expected <ip> <port> <team>' >&2
        exit 1
    fi
    # BASH_ARGV is reversed??
    IP=${BASH_ARGV[2]}
    PORT=${BASH_ARGV[1]}
    TEAM=${BASH_ARGV[0]}
}

set_http_base() {
    HTTP_BASE="$1"
}

set_http_host() {
    HTTP_HOST="$1"
}

http_req() {
    METHOD="$1"
    shift
    URL="$1"
    shift

    if [[ "x$HTTP_HOST" -ne "x" ]]
    then
        curl -s -X "$METHOD" -H "Host: $HTTP_HOST" "$HTTP_BASE$URL" "$@"
    else
        curl -s -X "$METHOD" "$HTTP_BASE$URL" "$@"
    fi
}

http_post() {
    http_req GET "$@"
}

http_get() {
    http_req GET "$@"
}

http_put() {
    http_req PUT "$@"
}

http_delete() {
    http_req DELETE "$@"
}

http_head() {
    http_req HEAD "$@" -I
}

http_options() {
    http_req OPTIONS "$@"
}

get_http_header() {
    shopt -s extglob # Required to trim whitespace; see below

    while IFS=':' read key value; do
        if [[ "$key" == "$1" ]]
        then
            # trim whitespace in "value"
            value=${value##+([[:space:]])}; value=${value%%+([[:space:]])}
            echo $value
        fi
    done
}
