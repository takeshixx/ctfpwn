"""A module for shared instances."""
import logging
from .flagdb import FlagDB

LOG_LEVEL_STAT = logging.INFO + 1
logging.addLevelName(LOG_LEVEL_STAT, 'STATISTIC')

flag_db = FlagDB()
