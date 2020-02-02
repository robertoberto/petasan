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
from PetaSAN.core.common.enums import DiskUsage,OsdStatus

class DiskInfo(object):
    def __init__(self):
        self.name = ""
        self.size = ""
        self.is_ssd = False
        self.serial = ""
        self.model = ""
        self.vendor = ""
        self.type = ""
        self.usage = DiskUsage.no
        self.status = OsdStatus.no_status
        self.osd_id = -1
        self.osd_uuid = ""
        self.error_message = ""
        self.linked_journal = ""
        self.linked_osds = []
        self.smart_test = ""
        self.linked_journal_part_num = -1
        self.linked_cache = []
        self.linked_cache_part_num = []
        self.lv_name = ""
        self.vg_name = ""
        self.no_of_partitions = -1
        self.no_available_partitions = -1

    def load_json(self, j):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=True, indent=4)
        return j

    def get_dict(self):
        return self.__dict__

