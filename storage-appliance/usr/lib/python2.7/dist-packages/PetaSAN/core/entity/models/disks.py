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


from json import JSONEncoder

class add_disk_form(object):
    def __init__(self):

        self.id = ""
        self.IqnVal = ""
        self.Password = ""
        self.UserName = ""
        self.diskName = ""
        self.diskSize = 1
        self.orpACL = "All"
        self.orpAuth = "No"
        self.orpUseFirstRange = "Yes"
        self.path1 = ""
        self.path2 = ""
        self.ActivePaths = 2
        self.ISCSISubnet = "3"
        self.pool = ""
        self.data_pool = None
        self.is_replication_target = False
        self.replication_info = {}


    def load_json(self,j):
            self.__dict__ = json.loads(j)
            if not hasattr(self, 'is_replication_target'):
                self.is_replication_target = False
            if not hasattr(self, 'replication_info'):
                self.replication_info = {}

class Subnet_Info(object):
    def __init__(self):
        self.subnet = ""
        self.ip_min = ""
        self.ip_max = ""

    def load_json(self,j):
            self.__dict__ = json.loads(j)