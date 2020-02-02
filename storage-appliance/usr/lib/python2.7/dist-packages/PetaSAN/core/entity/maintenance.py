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


class MaintenanceConfig(object):
    def __init__(self):
        # The next properties will get and set from ceph directly.
        self.osd_recover = -1
        self.osd_out = -1
        self.osd_rebalance = -1
        self.osd_backfill = -1
        self.osd_down = -1
        self.osd_pause = -1
        self.osd_scrub = -1
        self.osd_deep_scrub = -1
        # The next properties will set and get from consul kv
        self.fencing= 1

    def read_json(self, j):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self.__dict__)
        return j

class MaintenanceStatus(object):
    def __init__(self):
        self.enable =0

    def read_json(self, j):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self.__dict__)
        return j
