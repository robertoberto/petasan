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

from consul import Consul
from PetaSAN.core.common.enums import ManageDiskStatus
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.consul.base import BaseAPI

def add_disk():
    api = ConsulAPI()
    print api.add_disk_resource("00101","")
    print api.add_disk_resource("00101/0","")
    print api.add_disk_resource("00101/1","")
    print api.add_disk_resource("00101/2","")

    print api.add_disk_resource("00001","")
    print api.add_disk_resource("00001/0","")
    print api.add_disk_resource("00001/1","")
    print api.add_disk_resource("00001/2","")



    print api.add_disk_resource("09001","")
    print api.add_disk_resource("09001/0","")
    print api.add_disk_resource("09001/1","")
    print api.add_disk_resource("09001/2","")


    print api.add_disk_resource("00002","")
    print api.add_disk_resource("00002/0","")
    print api.add_disk_resource("00002/1","")
    print api.add_disk_resource("00002/2","")

    pass


def get_consul_data():
    api = ConsulAPI()
    ob= api.find_disk("00001")
    if ManageDiskStatus.error == ob:
        print("error get consul data")
    else:
        print ob

def get_list():
    api = ConsulAPI()
    x= api.get_disk_kvs()
    for i in x:
        print i.Key



def is_resource_lock():
    api= ConsulAPI()
    api.is_path_locked_by_session("image00001","12761283-76ad-7c9c-08cc-f24ce539648e")

#add_disk()
#get_consul_data()
#add_disk()
#get_consul_data()

#xx =[x for x in  ConsulAPI().disk_paths_list().values() if x.Key.replace("/","+") ]
#print ConsulAPI().is_disk_exist("00002")
#is_resource_lock()

#print BaseAPI().read_recurse("PetaSAN/Disks/")

ConsulAPI().delete_disk("PetaSAN/Disks/",recurse=True)
#get_list()


