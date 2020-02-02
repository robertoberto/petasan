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

from PetaSAN.core.cache.cache import Cache
from PetaSAN.core.cache.cache_manager import CacheManager
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.cluster import PreConfigStorageDisks
from flask import json
import sys
from time import sleep, time
from PetaSAN.core.ceph.ceph_disk_lib import *
from PetaSAN.core.common.cmd import *
from PetaSAN.core.common.log import logger
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.entity.status import StatusReport
from PetaSAN.core.ceph import ceph_osd, ceph_disk_lib
from PetaSAN.core.lvm import lvm_lib
from PetaSAN.core.lvm.lvm_lib import rename_vg


def __get_pre_config_disks():
    disks = PreConfigStorageDisks()

    try:
        with open(ConfigAPI().get_node_pre_config_disks(), 'r') as f:
            data = json.load(f)
            disks.load_json(json.dumps(data))
            return disks
    except:
        return disks


# print subprocess.call("ceph-disk prepare --cluster ceph --zap-disk --fs-type xfs /dev/sdj /dev/sdh",shell=True)
cluster_name = configuration().get_cluster_name()
status = StatusReport()

status.success = False

try:
    cm = CacheManager()
    node_name = configuration().get_node_info().name
    storage_engine = configuration().get_cluster_info().storage_engine
    if configuration().get_node_info().is_storage:
        disks = __get_pre_config_disks()

        if len(disks.journals) > 0:
            for d in disks.journals:
                ceph_disk_lib.clean_disk(d)
                add_journal(d)

        if len(disks.caches) > 0:
            for cache_disk in disks.caches:
                ceph_disk_lib.clean_disk(cache_disk.keys()[0])
                ceph_disk_lib.add_cache(cache_disk.keys()[0])

        journal = ""
        cache = ""
        cache_type = ""

        for disk_name in disks.osds:
            device_name = disk_name
            ceph_disk_lib.clean_disk(disk_name)

            if len(disks.journals) == 0:
                journal = ""
                if storage_engine == "filestore":
                    # manually create journal partition in the same disk for filestore
                    journal_part_num = ceph_disk.create_journal_partition(device_name, external=False)
                    journal = ceph_disk.get_partition_name(device_name, journal_part_num)

            elif len(disks.journals) > 0:
                journal = get_valid_journal(journal_list=disks.journals)
                if journal is None:
                    status.failed_tasks.append("core_scripts_admin_add_osd_journal_err")
                    break

            if len(disks.caches) == 0:
                cache = ""
            elif len(disks.caches) > 0:
                cache_disk_list = [d.keys()[0] for d in disks.caches]
                cache = get_valid_cache(cache_list=cache_disk_list)

                if not cache:
                    status.failed_tasks.append("core_scripts_admin_add_osd_cache_err")
                    break

                cache_type = [d[cache] for d in disks.caches if cache in d][0]

            main_path = None
            vg_name = None
            cache_part = None
            if cache is not None and len(cache) > 0:
                main_path, cache_part = cm.create(disk_name, cache, cache_type)

            if main_path and cache_part:
                vg_name = main_path.split("/")[0]
                device_name = main_path

            if not ceph_disk_lib.prepare_osd(device_name, journal):
                if cache_part:
                    cm.delete(disk_name, cache_type)
                    clean_disk(disk_name)
                    clean_disk(cache_part)
                    set_cache_part_avail(cache_part)

                status.failed_tasks.append(
                    "scripts_create_osd_disk_prepare_failure_node" + "%" + str(disk_name) + "%" + str(node_name))
            else:
                logger.info("Successfully executed ceph-volume prepare for {}".format(disk_name))

            # wait_for_osd_up(disk_name)
        status.success = True

    else:
        status.success = True
except Exception as ex:
    if not status.success:
        status.failed_tasks.append("scripts_create_osd_disk_failure_node" + "%" + str(node_name))

sys.stdout.write("{} /report/".format(node_name))
sys.stdout.write(status.write_json())
sys.stdout.flush()
sys.stdout.close()

if status.success:
    sys.exit(0)
else:
    sys.exit(-1)
