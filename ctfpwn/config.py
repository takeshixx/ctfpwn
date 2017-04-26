# encoding: utf8
import pathlib
import time
import logging
import logging.config

import yaml


log = logging.getLogger(__name__)


class ReloadableConfig:
    """
    Config proxy which automatically reloads itself
    if the modification timestamp of the config file
    was changed
    """
    def __init__(self, configfile, logging_section):
        if not isinstance(configfile, pathlib.Path):
            configfile = pathlib.Path(configfile)
        self.configfile = configfile
        self.last_load = 0
        self.conf = {}
        self.logging_section = logging_section

    def load(self):
        """
        (Re)Load the configfile
        """
        try:
            with self.configfile.open() as fp:
                self.conf = yaml.load(fp)
        except yaml.YAMLError:
            log.exception('Error during config load')
        else:
            self.last_load = time.time()
            if 'logging' in self.conf and self.logging_section in self.conf['logging']:
                logging.config.dictConfig(self.conf['logging'][self.logging_section])
                log.info('Logging configured from %s', self.logging_section)
            else:
                log.warning('Logging default used')
            log.info('Loaded configuration file %s', str(self.configfile))

    @property
    def was_changed(self):
        """
        Compares the modification timestamp against the
        last load timestamp
        """
        return self.configfile.stat().st_mtime > self.last_load

    def __getitem__(self, name):
        if self.was_changed:
            self.load()
        return self.conf[name]

    def __len__(self):
        return len(self.conf)

    def __iter__(self):
        return iter(self.conf)

    def __contains__(self, name):
        if self.was_changed:
            self.load()
        return name in self.conf

    def __getattr__(self, name):
        if self.was_changed:
            self.load()
        return getattr(self.conf, name)
