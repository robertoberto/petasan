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

from PetaSAN.backend import manage_disk
from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.backend.manage_pools import ManagePools

from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.common.CustomException import ConsulException
from PetaSAN.core.common.log import logger
from time import sleep
import sys


def _get_pool_info_by_name(pool_name):
    manage_pools = ManagePools()
    pool_list = manage_pools.get_pools_info()
    for pool_info in pool_list:
        if pool_info.name == pool_name:
            return pool_info


def _get_running_pool_disks(pool):
    consul = ConsulAPI()
    running_pool_disks = []
    meta_disk = ManageDisk().get_disks_meta()

    pool_disks = set()
    pool_info = _get_pool_info_by_name(pool)

    if pool_info.type == "replicated":
        if len(meta_disk) > 0:
            for meta in meta_disk:
                if meta.pool == pool:
                   pool_disks.add(meta.id)

    elif pool_info.type == "erasure":
        if len(meta_disk) > 0:
            for meta in meta_disk:
                if meta.data_pool == pool:
                    pool_disks.add(meta.id)


    running_disks = consul.get_running_disks()
    for running_disk in running_disks :
        if running_disk in pool_disks :
            running_pool_disks.append(running_disk)


    return running_pool_disks


def _stop_disk(disk_id):
    try:
        consul_api = ConsulAPI()
        kv = consul_api.find_disk(disk_id)
        if not kv:
            return
        #consul_api.add_disk_resource(disk_id, 'disk', 1, kv.CreateIndex)
        consul_api.add_disk_resource(disk_id, 'disk', 1, kv.ModifyIndex)
    except Exception as ex:
        logger.error('Error stopping disk:{} {}'.format(disk_id,ex.message))
        raise ConsulException(ConsulException.GENERAL_EXCEPTION,'General Consul Error')


def _stop_pool_disks(pool,wait_interval=10,wait_count=10):

    running_pool_disks = _get_running_pool_disks(pool)
    if len(running_pool_disks) == 0 :
        return
    logger.info('Stop pool disks count {}'.format( str(len(running_pool_disks)) ))
    for disk in running_pool_disks:
        logger.info('Stopping pool disk {}'.format(disk) )
        _stop_disk(disk)

    while 0 < wait_count:
        sleep(wait_interval)
        running_pool_disks = _get_running_pool_disks(pool)
        logger.info('Stop pool disks count {}'.format( str(len(running_pool_disks)) ))
        if len(running_pool_disks) == 0 :
            return
        wait_count -= 1



if len(sys.argv) != 3 or sys.argv[2] != '--yes-i-really-really-mean-it' :
    print 'usage: delete_pool pool --yes-i-really-really-mean-it '
    sys.exit(1)


pool = sys.argv[1]


# step 1 stop disks
_stop_pool_disks(pool)
sleep(20)

# step 2 delete disks in case of ec
pool_info = _get_pool_info_by_name(pool)
if pool_info.type == "erasure":
    meta_disk = ManageDisk().get_disks_meta()
    if len(meta_disk) > 0:
        for disk in meta_disk:
            if disk.data_pool == pool:
                ManageDisk().delete_disk(disk.id, disk.pool)

# step 3 delete pool
ceph_api = CephAPI()
ceph_api.delete_pool(pool)







