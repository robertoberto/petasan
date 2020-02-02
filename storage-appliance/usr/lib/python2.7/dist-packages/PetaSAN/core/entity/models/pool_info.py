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


class PoolInfo(object):
    def __init__(self):
        self.compression_algorithm = "none"
        self.compression_mode = "none"
        self.id = 0
        self.name = ""
        self.pg_num = 64
        self.pgp_num = 64
        self.min_size = 2
        self.size = 2
        self.rule_id = 0
        self.rule_name = ""
        self.ec_profile = ""
        self.type = "replicated"
        self.active_osds = 0

