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

    def timestamp(self):
        return time.strftime('%H:%M:%S')

    def warning(self,msg):
        print('{D}[{E}{C}WARNING{E}{D}]{E} {D}[{E}{C}{T}{E}{D}]{E} {S}'.format(
                E=self.c_escape,D=self.c_delimiter,C=self.c_warn,T=self.timestamp(),S=str(msg))
        )

    def error(self,msg):
        print('{D}[{E}{C}WARNING{E}{D}]{E} {D}[{E}{C}{T}{E}{D}]{E} {S}'.format(
                E=self.c_escape,D=self.c_delimiter,C=self.c_error,T=self.timestamp(),S=str(msg))
        )

    def debug(self,msg):
        if self.DEBUG:
            print('{D}[{E}{C}DEBUG{E}{D}]{E} {D}[{E}{C}{T}{E}{D}]{E} {S}'.format(
                E=self.c_escape,D=self.c_delimiter,C=self.c_debug,T=self.timestamp(),S=str(msg))
            )

    def info(self,msg):
        print('{D}[{E}{C}INFO{E}{D}]{E} {D}[{E}{C}{T}{E}{D}]{E} {S}'.format(
                E=self.c_escape,D=self.c_delimiter,C=self.c_info,T=self.timestamp(),S=str(msg))
        )

    def score(self,msg):
        print('{D}[{E}{C}SCORED{E}{D}]{E} {D}[{E}{C}{T}{E}{D}]{E} {S}'.format(
                E=self.c_escape,D=self.c_delimiter,C=self.c_score,T=self.timestamp(),S=str(msg))
        )

    def stats(self,msg):
        print('*'*90)
        print('{D}[{E}{C}STATS{E}{D}]{E} {D}[{E}{C}{T}{E}{D}]{E} {S}'.format(
                E=self.c_escape,D=self.c_delimiter,C=self.c_stats,T=self.timestamp(),S=str(msg))
        )
        print('*'*90)


log = TinyLogs(debug=True)