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


class DestinationCluster(object):
    def __init__(self):
        self.cluster_name = ""
        self.remote_ip = ""
        self.ssh_private_key = ""
        self.user_name = ""
        self.cluster_fsid = ""

    def load_json(self, j=""):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4, ensure_ascii=False).encode('utf8')
        return j
