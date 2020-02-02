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

from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.cmd import *
from PetaSAN.core.entity.cluster import NodeInfo
import json
from PetaSAN.core.config.api import ConfigAPI

config = configuration()
node = config.get_node_info()
cluster = config.get_cluster_info()

conf = configuration()
cluster_info = conf.get_cluster_info()

first_cluster_node = cluster_info.management_nodes[0]
first_node_info=NodeInfo()
first_node_info.load_json(json.dumps(first_cluster_node))

second_cluster_node = cluster_info.management_nodes[1]
second_node_info=NodeInfo()
second_node_info.load_json(json.dumps(second_cluster_node))

call_cmd('python'+ConfigAPI().get_consul_start_up_script_path()+' " -retry-join 192.168.17.14"')