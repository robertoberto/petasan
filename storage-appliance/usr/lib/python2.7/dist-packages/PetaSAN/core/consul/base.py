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

from PetaSAN.core.consul.ps_consul import Consul
from PetaSAN.core.common.log import logger
import datetime

class BaseAPI:

    #root = ""

    def __int__(self):
        pass

    def read_value(self, key):
        cons = Consul()
        index, data = cons.kv.get(key)
        if data is None:
            return None
        return data['Value']

    def write_value(self, key, value):
        cons = Consul()
        cons.kv.put(key, value)

    def delete_key(self, key,recurse = False):
        cons = Consul()
        cons.kv.delete(key,recurse)

    def read_recurse(self, key):
        cons = Consul()
        index, data = cons.kv.get(key,None,True)
        return data

    def watch(self, key, current_index):
        cons = Consul()
        return cons.kv.get(key, index=current_index, recurse=True)

