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


class ISCSISubnet(object):
    def __init__(self):
        self.subnet_mask = ''
        self.vlan_id = ''
        self.auto_ip_from = ''
        self.auto_ip_to = ''

    def read_json(self, j):
        self.__dict__ = json.loads(j)
        if not hasattr(self,'vlan_id'):
            self.vlan_id = ''

    def write_json(self):
        j = json.dumps(self.__dict__)
        return j

