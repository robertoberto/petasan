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

from PetaSAN.core.ceph.api import CephAPI
import subprocess
from PetaSAN.backend.manage_config import ManageConfig
from PetaSAN.core.entity.disk_info import DiskMeta


from PetaSAN.core.lio.network   import NetworkAPI
from PetaSAN.core.lio.api import LioAPI

def add_ip(ip,sub,eth , vlan_id):
    api = NetworkAPI()
    print api.add_ip(ip,sub,eth , vlan_id)


def del_ip(ip,sub,eth):
    api = NetworkAPI()
    print api.delete_ip(ip,sub,eth)

def add_target_without_auth_acl():
    api= LioAPI()
    disk =DiskMeta()
    disk.id="image00001"
    disk.ip="192.168.57.100"
    disk.ip2="192.168.57.102"
    disk.acl=""
    disk.iqn="image00001",ManageConfig().get_iqn_base()+":"+"image00001"
    api.add_target(disk)

def add_target_with_auth_m_acl():
    api= LioAPI()
    disk =DiskMeta()

    api.add_target(CephAPI().get_disk_meta("00001"))


def add_target_with_auth_without_acl():
    api= LioAPI()
    disk =DiskMeta()
    disk.id="image00001"
    disk.ip="192.168.57.100"
    disk.ip2="192.168.57.102"
    disk.acl=""
    disk.password="password1234"
    disk.user="test"
    disk.iqn="image00001",ManageConfig().get_iqn_base()+":"+"image00001"
    api.add_target(disk)



def get_ips():
    api= LioAPI()
    api.get_target_ips(":".join([ManageConfig().get_iqn_base(),"image00001"]))



#add_ip("192.168.57.100","255.255.255.0","eth0")
#del_ip("192.168.57.100","255.255.255.0","eth0")

#add_target_with_auth_m_acl()
#add_target_without_auth_acl()
#add_target_with_auth_without_acl()
#add_target_without_auth_acl()
#delete_target()

#get_ips()
#print ManageConfig().get_iqn_base()

'''p =subprocess.Popen(["ip", "address", "del", "192.168.57.61", "dev", "eth0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out = p.stderr.read()
print "err  "+out'''

#add_target_with_auth_m_acl()
'''
#LioAPI().delete_target("image-00001",CephAPI().get_disk("00001").iqn)
print LioAPI().get_target_ip_list(CephAPI().get_disk("00001").iqn)
LioAPI().set_tpg_status(CephAPI().get_disk("00001").iqn,1,False)
LioAPI().set_tpg_status(CephAPI().get_disk("00001").iqn,2,False)'''''
#xx=[disk_id.replace("image-","") for disk_id in LioAPI().get_list_storage()]
#print xx



from PetaSAN.backend.service import Service
xx= Service().__prioritize_paths()
pass