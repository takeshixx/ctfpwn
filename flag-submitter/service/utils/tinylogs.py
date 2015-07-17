"""Utils for general logging."""

from time import strftime

class TinyLogs:
    def __init__(self):
        self.c_warning = '\033[1;31m'
        self.c_debug = '\033[1;1m' 
        self.c_info = '\033[1;32m'
        self.c_stats = '\033[1;44m'
        self.c_escape = '\033[0m'
        self.c_delimiter = '\033[1;1m'
        self.DEBUG = False


    def timestamp(self):
        return strftime('%H:%M:%S')


    def warning(self,msg):
        print '{D}[{E}{C}WARNING{E}{D}]{E} {D}[{E}{C}{T}{E}{D}]{E} {S}'.format(
                E=self.c_escape,D=self.c_delimiter,C=self.c_warning,T=self.timestamp(),S=str(msg))


    def debug(self,msg):
        if self.DEBUG:
            print '{D}[{E}{C}DEBUG{E}{D}]{E} {D}[{E}{C}{T}{E}{D}]{E} {S}'.format(
                E=self.c_escape,D=self.c_delimiter,C=self.c_debug,T=self.timestamp(),S=str(msg))


    def info(self,msg): 
        print '{D}[{E}{C}SCORED{E}{D}]{E} {D}[{E}{C}{T}{E}{D}]{E} {S}'.format(
                E=self.c_escape,D=self.c_delimiter,C=self.c_info,T=self.timestamp(),S=str(msg))


    def stats(self,msg): 
        print '{D}[{E}{C}STATS{E}{D}]{E} {D}[{E}{C}{T}{E}{D}]{E} {S}'.format(
                E=self.c_escape,D=self.c_delimiter,C=self.c_stats,T=self.timestamp(),S=str(msg))
