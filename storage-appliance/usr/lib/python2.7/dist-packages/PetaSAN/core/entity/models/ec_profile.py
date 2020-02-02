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

class ECProfile(object):
    def __init__(self):
        self.name = ""
        self.k = -1
        self.m = -1
        self.locality = -1
        self.durability_estimator = -1
        self.plugin = ""
        self.packet_size = -1
        self.strip_unit = ""
        self.technique = ""
