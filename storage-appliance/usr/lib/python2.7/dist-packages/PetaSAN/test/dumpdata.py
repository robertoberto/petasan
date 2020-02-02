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
import flask
import pickle
from PetaSAN.core.ceph.util import get_next_id
from PetaSAN.core.entity.disk_info import DiskInfo, DiskMeta









xx = 10
if type(xx) == int:
     print "yes"


string_var = ""
if not string_var:
     print "not string"

xx =['xx501','','xx0410','xx0200']
xx= [weapon.replace("xx","") for weapon in xx]

print get_next_id (xx,8)