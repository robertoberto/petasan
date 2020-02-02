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

from flask import json


class DiskMeta(object):
    def __init__(self, dictionary=None):
        self.disk_name = ""
        self.description = ""
        self.acl = ""
        self.user = ""
        self.password = ""
        self.size = 0
        self.iqn = ""
        self.create_date = ""
        self.id = ""
        self.pool = ""
        self.paths = []
        self.wwn = ""
        self.data_pool = ""
        self.is_replication_target = False
        self.replication_info = {}

        if dictionary:
            for key in dictionary:
                setattr(self, key, dictionary[key])

    def load_json(self, j):
        self.__dict__ = json.loads(j)
        if not hasattr(self, 'data_pool'):
            self.data_pool = ''
        if not hasattr(self, 'is_replication_target'):
            self.is_replication_target = False
        if not hasattr(self, 'replication_info'):
            self.replication_info = {}

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=True, indent=4)
        return j

    def get_paths(self):
        """

        :rtype : [Path]
        """
        paths = []
        for i in self.paths:
            path = Path()
            path.load_json(json.dumps(i))
            paths.append(path)
        return paths


class DiskInfo(object):
    def __init__(self):
        self.disk_name = ""
        self.description = ""
        self.acl = ""
        self.user = ""
        self.password = ""
        self.size = 0
        self.create_date = ""
        self.id = 0
        self.paths = []
        self.status

    def load_json(self, j=""):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=True, indent=4)
        return j


class Path(object):
    def __init__(self):
        self.ip = ""
        self.subnet_mask = ""
        self.eth = ""
        self.vlan_id = ""
        self.locked_by = ""

    def load_json(self, j=""):
        self.__dict__ = json.loads(j)
        if not hasattr(self, 'vlan_id'):
            self.vlan_id = ''

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=True, indent=4)
