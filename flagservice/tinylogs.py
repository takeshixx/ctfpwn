from __future__ import print_function
import sys
import time


class TinyLogs:
    def __init__(self, debug=False):
        self.c_error = '\033[1;31m'
        self.c_warn = '\033[93m'
        self.c_debug = '\033[1;1m'
        self.c_info = '\033[94m'
        self.c_score = '\033[1;32m'
        self.c_stats = '\033[1;44m'
        self.c_escape = '\033[0m'
        self.c_delimiter = '\033[1;1m'
        self.DEBUG = debug

        self.warn = self.warning
        self.err = self.error
        self.msg = self.info

    def timestamp(self):
        return time.strftime('%H:%M:%S')

    def warning(self, msg):
        print('[WARNING] [{}] {}'.format(self.timestamp(), str(msg)))

    def error(self, msg):
        print('[ERROR] [{}] {}'.format(self.timestamp(), str(msg)), file=sys.stderr)

    def debug(self, msg):
        if self.DEBUG:
            print('[DEBUG] [{}] {}'.format(self.timestamp(), str(msg)))

    def info(self, msg):
        print('[INFO] [{}] {}'.format(self.timestamp(), str(msg)))

    def score(self, msg):
        print('[SCORE] [{}] {}'.format(self.timestamp(), str(msg)))

    def stats(self, msg):
        print('[STATS] [{}] {}'.format(self.timestamp(), str(msg)))


log = TinyLogs(debug=True)
