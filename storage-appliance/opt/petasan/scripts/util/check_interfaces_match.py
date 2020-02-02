#! /usr/bin/python
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

from PetaSAN.core.cluster.network import Network
from PetaSAN.core.cluster.configuration import configuration

config = configuration().get_cluster_info()
net = Network()
eths = net.get_node_interfaces()

print('cluster management interface  ' + config.management_eth_name )
print('node management interface  ' + net.get_node_management_interface())

if config.management_eth_name == net.get_node_management_interface():
    print('management interface match')
else:
    print('Error: management interface mis-match !!')

print ('cluster eth count ' + str(config.eth_count) )
print ('node eth count    ' + str(len(eths)) )

if config.eth_count == len(eths):
    print('eth count match')
else:
    print('Error: eth count mis-match !!')

print('detected interfaces')
for eth in eths:
    print(eth.name)

