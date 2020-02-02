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


########################################################
# script to start all stopped iSCSI disks
# place in /opt/petasan/scripts/util/start_all_disks.py
########################################################

from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.entity.disk_info import DiskMeta
from PetaSAN.core.common.enums import Status


def stop_disk(id,pool):
    manage_disk = ManageDisk()
    if manage_disk.stop(id) == Status.done:
        return True
    return False


def is_disk_started(id):
    consul_api = ConsulAPI()
    status = consul_api.find_disk(id)
    if status is not None:
        return True
    return False


def stop_all_disks():
    ceph_api = CephAPI()
    disks = ceph_api.get_disks_meta()
    if disks is None:
        print('Error reading disk metadata from Ceph')
        return False
    disks.sort(key=lambda disk: disk.id) 
    for disk_meta in disks:
        if is_disk_started(disk_meta.id):
            if stop_disk(disk_meta.id,disk_meta.pool):
                print "Stopped disk " + disk_meta.id + " " + disk_meta.disk_name
            else:
                print "Error stopping disk " + disk_meta.id + " " + disk_meta.disk_name
    return True


if __name__ == "__main__":
    stop_all_disks()



