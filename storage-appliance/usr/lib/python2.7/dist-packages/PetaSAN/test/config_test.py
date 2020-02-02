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


from PetaSAN.core.config.api import *
from PetaSAN.core.entity.app_config import AppConfig
from PetaSAN.core.entity.subnet_info import SubnetInfo
from PetaSAN.core.entity.iscsi_subnet import ISCSISubnet
from PetaSAN.backend.manage_config import ManageConfig
from PetaSAN.core.common.enums import PathType


#  -------- ConfigAPI test --------------------
api = ConfigAPI()
# get static configuration
print api.get_ceph_conf_path()
print api.get_consul_watch_sleep_max()

api.delete_app_config()


# save  complete app configuration object
conf1 = AppConfig()
conf1.iscsi1_subnet_mask = '255.255.255.0'
conf1.iscsi1_auto_ip_from = '192.168.57.1'
conf1.iscsi1_auto_ip_to = '192.168.57.200'
conf1.iscsi2_subnet_mask = '255.255.255.0'
conf1.iscsi2_auto_ip_from = '192.168.58.1'
conf1.iscsi2_auto_ip_to = '192.168.58.200'
api.write_app_config(conf1)

# read complete app configuration
conf2 = api.read_app_config()
print conf2.iscsi1_subnet_mask
print conf2.iscsi1_auto_ip_from
print conf2.iscsi1_auto_ip_to


#  -------- ManageConfig test --------------------
config = ManageConfig()


# read iscsi 1 subnet
subnet1 = config.get_iscsi1_subnet()
print subnet1.auto_ip_to

# write iscsi2 subnet
subnet2 = ISCSISubnet()
subnet2.subnet_mask = '255.255.255.0'
subnet2.auto_ip_from = '192.168.59.1'
subnet2.auto_ip_to = '192.168.59.200'
config.set_iscsi2_subnet(subnet2)

# valid new ips
ips = ['192.168.57.100','192.168.57.101','192.168.57.103']
# 1 = valid, -3 = invalid_count,  -2 = wrong subnet, -1 = used already
print config.validate_new_iscsi_ips(ips,PathType.iscsi_subnet1)

# get new ips
path_list =  config.get_new_iscsi_ips(PathType.both,4)
for p in path_list:
    print p.ip




