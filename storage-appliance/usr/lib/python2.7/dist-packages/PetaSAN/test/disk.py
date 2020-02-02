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
import pickle
from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.core.common.enums import PathType

from PetaSAN.core.entity.disk_info import DiskMeta, Path
from PetaSAN.core.common.log import logger



from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.ceph.api import ManageDiskStatus
from PetaSAN.core.config.api import ConfigAPI
app_conf = ConfigAPI()


def create_disk(disk_id):
    ceph_api = CephAPI()
    manage_disk = ManageDisk()
    disk_meta=  DiskMeta()
    disk_meta.disk_name ="sanatech" + str("sql1")
    disk_meta.size=1
    disk_meta.password="123"
    disk_meta.user="mostafa"

    path1=  Path()
    path2=  Path()
    path1.ip="192.168.57.150"
    path1.subnet_mask="255.255.255.0"
    path1.eth="eth0"
    path2.ip="192.168.58.150"
    path2.subnet_mask="255.255.255.0"
    path2.eth="eth1"
    disk_meta.paths.append(path1)
    disk_meta.paths.append(path2)
    disk_meta.id=disk_id
    disk_meta.iqn=app_conf.read_app_config().iqn_base +":"+disk_meta.id
    status = ceph_api.add_disk(disk_meta)

    if status == ManageDiskStatus.done:
        logger.info("done , create disk")
        attr = ceph_api.read_image_metadata("image-"+disk_id)
        xx = attr.get(app_conf.get_image_meta_key())
        logger.info(xx)
        disk = DiskMeta()
        disk.load_json(xx)

        print("disk user is %s" % (disk.user))
        print  disk

    elif status == ManageDiskStatus.disk_name_exists:
        print("disk is Exists")
    else:
        print("error create disk")


def get_meta():
    ceph_confg = CephAPI()
    ceph_api = CephAPI()
    logger.info("done , create disk")
    attr = ceph_api.read_image_metadata("000001")
    xx = attr.get(app_conf.get_image_meta_key())
    logger.info(xx)
    disk = DiskMeta()
    disk.load_json(xx)

    logger.info("disk user is %s" % (disk.user))


def get_list():
    ceph_api = CephAPI()
    for i in ceph_api.get_disks_meta():

        print i.user ,i.disk_name,i.password
        for p in i.get_paths():

            print p.ip,p.subnet_mask,p.eth


def manage_disk_add_disk(name):
    manage_disk = ManageDisk()
    disk_meta=  DiskMeta()
    disk_meta.disk_name ="sanatech" + str(name)
    disk_meta.size=1
    #disk_meta.password="password123456"
    #disk_meta.user="mostafa"
    status = manage_disk.add_disk(disk_meta,None,PathType.both,2)
    logger.info(status)


def manage_disk_add_disk_ips(name):
    manage_disk = ManageDisk()
    disk_meta=  DiskMeta()
    disk_meta.disk_name ="sanatech" + str(name)
    disk_meta.size=1
    disk_meta.password="password123456"
    disk_meta.user="mostafa"
    ips =[]
    ips.append("192.168.57.200")
    ips.append("192.168.57.201")
    status = manage_disk.add_disk(disk_meta,ips,PathType.both,2,False,False)
    logger.info(status)

def get_list_status():
    ceph_manage = ManageDisk()
    ceph_manage.get_disks_meta()
    for i in ceph_manage.get_disks_meta():
        if "mostafa" == i.user:
            logger.info("disk found")
        try:
            print i.user ,i.disk_name,i.ip,i.ip2,i.subnet1,i.subnet2,i.password,i.id,i.status,i.iqn,i.size
        except Exception as x:
            pass

def test_is_image_busy(image):
    ceph_api = CephAPI()
    if ceph_api.is_image_busy(image):
        print  "busy"
    else:
        "not busy"


def stop_disk(id):
    ceph_manage = ManageDisk()
    ceph_manage.stop(id)

def start_disk(id):
    ceph_manage = ManageDisk()
    ceph_manage.start(id)

def meta(id):
    ceph_api = CephAPI()
    ceph_api.read_image_metadata(id)

    pass

def list():
    ceph_api = CephAPI()
    ceph_api.get_disks_meta()

    pass

def delete(disk_id):
    manage_disk = ManageDisk()
    print manage_disk.delete_disk(disk_id)
#create_disk()
# get_meta()
def deattach_disk(disk_id):
    ceph_manage = ManageDisk()
    ceph_manage.detach_disk(disk_id)
    disk =ceph_manage.get_disk(disk_id)
    print disk.id,disk.disk_name,disk.size,[ p for p in disk.paths]



def attach_diskk(disk_id):
    manage_disk = ManageDisk()
    disk_meta=  DiskMeta()
    disk_meta.id = disk_id
    disk_meta.disk_name ="mostafa07"
    disk_meta.size=6
    status = manage_disk.attach_disk(disk_meta,None,PathType.both,2)
    print(status)
    disk =manage_disk.get_disk(disk_id)
    print disk.id,disk.disk_name,disk.size,[ p for p in disk.paths]

def get_disk_info(disk_id):
    manage_disk = ManageDisk()
    i=manage_disk.get_disk(disk_id)
    print i.user ,i.disk_name,i.ip,i.ip2,i.subnet1,i.subnet2,i.password,i.id,i.iqn,i.size

def update_disk(disk_id,name):
    manage_disk = ManageDisk()
    disk_meta=  DiskMeta()
    disk_meta.disk_name ="sanatech" + str(name)
    disk_meta.size=3
    disk_meta.id = disk_id
    #disk_meta.password="password123456"
    #disk_meta.user="mostafa"
    status = manage_disk.edit_disk(disk_meta,True)
    print status

    disk =manage_disk.get_disk(disk_id)
    print disk.id,disk.size,[ p for p in disk.paths]


#manage_disk_add_disk(1)
#manage_disk_add_disk(2)
#manage_disk_add_disk(3)
#manage_disk_add_disk(3)
#get_list_status()
#deattach_disk("00004")
#attach_diskk("00004")
#update_disk("00004")

#test_is_image_busy("image00001")

#start_disk("image00001")
#stop_disk("image00001")
#list()
#delete("00002")
#get_list_status()
#get_disk_info("00004")


#create_disk("00001")




manage_disk_add_disk("_sql")
#update_disk("00001","_sqlcc")
#deattach_disk("00001")
#attach_diskk("00001")
#start_disk("00001")
#stop_disk("00001")
#delete("00001")
#manage_disk_add_disk_ips("_sql")



#get_list()
#CephAPI().map_iamge("image-00001")


