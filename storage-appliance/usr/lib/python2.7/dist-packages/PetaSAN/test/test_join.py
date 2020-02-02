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
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.cluster import NodeInfo


from PetaSAN.backend.cluster.deploy import Wizard

def test_join(ip,password):
    wiz = Wizard()

    print wiz.join(ip,password)
    #test_set_Node()
    wiz.build()


test_join("192.168.57.10","password")
'''conf = configuration()
current_node_name = conf.get_node_info().name
clu = conf.get_cluster_info()
config_api = ConfigAPI()
for i in clu.management_nodes:
    node_info=NodeInfo()
    node_info.load_json(json.dumps(i))
    if node_info.name != current_node_name:
        pass
            #ssh_obj = ssh()
            #ssh_obj.copy_file_to_host(node_info.management_ip,config_api.get_cluster_info_file_path())'''
