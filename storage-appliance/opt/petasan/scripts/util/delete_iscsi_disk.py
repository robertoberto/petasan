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

import sys

from PetaSAN.core.common.CustomException import CephException
from PetaSAN.core.ceph.api import CephAPI

# sys.argv = script_name , disk_id, pool
from PetaSAN.core.ceph.replication.snapshots import Snapshots
from PetaSAN.core.common.enums import Status
from time import sleep
from PetaSAN.core.common.log import logger

if len(sys.argv) != 3:
    sys.exit(1)

image_name = sys.argv[1]
# disk_id = image_name.split("-")[1]
pool = sys.argv[2]
delete_snap_status = False
status = False

try:
    # get disk snapshots
    snapshots = Snapshots()
    snap_list = snapshots.get_disk_snapshots(pool, image_name)

    # delete disk snapshots
    if len(snap_list) > 0:
        delete_snap_status = snapshots.delete_snapshots(pool, image_name)
except:
    logger.error("Getting snapshots of image: " + image_name)
    pass

# delete disk
i = 1
ceph_api = CephAPI()

while i <= 10:
    busy = ceph_api.is_image_busy(image_name, pool)
    if busy:
        logger.info("Disk: {} is busy for ({}) times".format(image_name, i))
        sleep(15)  # wait 15 sec
        i += 1
    else:
        logger.info("Start deleting disk: {} ...".format(image_name))
        status = ceph_api.delete_disk(image_name, pool)
        if status == Status.error:
            raise CephException(CephException.GENERAL_EXCEPTION, 'Error Deleting Image: {}'.format(image_name))
        logger.info("Deleting disk: {} has been done".format(image_name))
        break

