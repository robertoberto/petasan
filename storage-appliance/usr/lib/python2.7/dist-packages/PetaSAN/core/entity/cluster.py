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



class ClusterInfo(object):
    def __init__(self):
        self.name=''
        self.management_eth_name=''
        self.iscsi_1_eth_name=''
        self.iscsi_2_eth_name=''
        self.backend_1_eth_name=''
        self.backend_2_eth_name=''
        self.backend_1_mask=''
        self.backend_1_base_ip=''
        self.backend_1_vlan_id = ''
        self.backend_2_mask=''
        self.backend_2_base_ip=''
        self.backend_2_vlan_id = ''
        self.eth_count=0
        self.management_nodes=[]
        self.jumbo_frames = []
        self.bonds = []
        self.storage_engine = 'bluestore'




    def load_json(self,j):
        self.__dict__ = json.loads(j)

        if not hasattr(self,'backend_1_vlan_id'):
            self.backend_1_vlan_id = ''

        if not hasattr(self,'backend_2_vlan_id'):
            self.backend_2_vlan_id = ''

        if not hasattr(self,'storage_engine'):
            self.storage_engine = 'bluestore'



    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)
        return j



class NodeInfo(object):
    def __init__(self):
        self.name=""
        self.management_ip = ""
        self.backend_1_ip = ""
        self.backend_2_ip = ""
        self.is_storage = True
        self.is_iscsi = True
        self.is_backup = False
        self.is_management = True



    def load_json(self,j):
        self.__dict__ = json.loads(j)
        if not hasattr(self, 'is_backup'):
            self.is_backup = False

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)
        return j

class PreConfigStorageDisks(object):
    def __init__(self):
        self.osds = []
        self.journals = []
        self.caches = []

    def load_json(self,j):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)
        return j
