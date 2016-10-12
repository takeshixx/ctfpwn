# $0 will contain the filename itself
TARGET_IP=$1
TARGET_PORT=$2

# echo will output to stdout. They will be retrieved with regex, so there is no
# special format needed. So you actually may print other stuff without breaking
# the flag retrieval.
echo "thisIsAFlag"
echo "thisIsAnotherFlag"

# You can indicate that something went wrong by using exit 1
# If you do so, your output will not be scanned for flags, so please only use
# this if something went completely wrong and your output does not contain any
# flags.
