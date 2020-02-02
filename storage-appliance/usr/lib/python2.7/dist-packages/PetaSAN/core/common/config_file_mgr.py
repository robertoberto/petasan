#!/usr/bin/python
'''
 Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
 Copyright (C) 2019 PetaSAN www.petasan.org


 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU Affero General Public License
 as published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU Affero General Public License for more details.
'''

from ConfigParser import ConfigParser
from PetaSAN.core.cluster.configuration import configuration


class ConfigFileMgr(object):
    def __init__(self):
        self.cluster_name = configuration().get_cluster_name()
        self.config_file_path = '/etc/ceph/' + self.cluster_name + '.conf'
        self.config = ConfigParser()
        self.config.read(self.config_file_path)

    def print_debug(self):
        out = ""
        self.config.read(self.config_file_path)
        for section in self.config.sections():
            out += "[%s] \n" % section
            for options in self.config.options(section):
                out += "%s = %s \n" % (options, self.config.get(section, options))
            out += "\n"
        print out

    def add_option(self, section, option, value):
        self.config.set(section, option, value)

    def remove_option(self, section, option):
        if self.config.has_option(section, option):
            self.config.remove_option(section, option)

    def save_config_file(self):
        with open(self.config_file_path, 'w+') as configfile:
            self.config.write(configfile)


"""
cfg = ConfigFileMgr()
cfg.add_option('global', 'test', 1)
cfg.add_option('global', 'test2', 'ceph')
cfg.save_config_file()
cfg.print_debug()
"""

