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


class PathAssignmentInfo(object):
    def __init__(self):
        self.ip = ""
        self.disk_id = ""
        self.disk_name = ""
        self.node = ""
        self.status = -1
        self.target_node = ""
        self.interface = ""

    def load_json(self, j=""):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=True, indent=4)
        return j


class AssignmentStats(object):
    def __init__(self):
        self.paths = []
        self.is_reassign_busy = False
        self.nodes = []

    def load_json(self, j=""):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=True, indent=4)

        return j