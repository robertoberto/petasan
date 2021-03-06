#!/usr/bin/python
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


from PetaSAN.core.ceph.pool_checker import PoolChecker
from flask import json


pc = PoolChecker()
active_osds = pc.get_active_osds()
print( json.dumps(active_osds) )

# print('\n')
# print('//////////////////////////////////////////////////////////////////////////////')
# print('Output of Script :')
# print( json.dumps(active_osds) )
# print('//////////////////////////////////////////////////////////////////////////////')

