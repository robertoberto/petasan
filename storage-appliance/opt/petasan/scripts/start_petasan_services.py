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
from time import sleep
from PetaSAN.core.common.cmd import *
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.cluster.ntp import NTPConf
from PetaSAN.core.cluster.job_manager import JobManager
from ceph_volume.api.lvm import *
from PetaSAN.core.cache.cache_manager import CacheManager
from PetaSAN.core.ceph import ceph_disk_lib



def startup_services(building_stage=False, cluster_complete=False):
    path = ConfigAPI().get_service_files_path()

    if not building_stage and cluster_complete:
        logger.info("Start settings IPs")
        call_cmd('python ' + ConfigAPI().get_node_start_ips_script_path())

        call_cmd('systemctl start ntp')
        call_cmd('systemctl start petasan-mount-sharedfs')
        NTPConf().force_ntp_sync()
        JobManager().remove_jobs_since(0)

        if cluster_config.get_node_info().is_management:
            call_cmd('python ' + ConfigAPI().get_consul_start_up_script_path())
            call_cmd('systemctl start glusterd')
            call_cmd('systemctl start petasan-cluster-leader')
        else:
            call_cmd('python ' + ConfigAPI().get_consul_client_start_up_script_path())

        logger.info("Starting cluster file sync service")
        call_cmd('systemctl start petasan-file-sync')

        call_cmd('/opt/petasan/scripts/load_iscsi_mods.sh')
        if cluster_config.get_node_info().is_iscsi:
            logger.info("Starting iSCSI Service")
            call_cmd('systemctl start petasan-iscsi')

        if cluster_config.get_node_info().is_management:
            logger.info("Starting Cluster Management application")
            call_cmd('systemctl start petasan-admin')
            # create Ceph manager if not already created
            # exec_command('python /opt/petasan/scripts/create_mgr.py 60 >/dev/null 2>&1 &')

        logger.info("Starting Node Stats Service")
        call_cmd('systemctl start petasan-node-stats')

        # activate PetaSAN custom vgs
        cm = CacheManager()
        cm.activate()

        # remove any unused ceph-volume services
        ceph_disk_lib.delete_unused_ceph_volume_services()

        logger.info("Starting OSDs")
        call_cmd('systemctl restart petasan-start-osds')


        if cluster_config.get_node_info().is_backup:
            logger.info('Starting sync replication node service')
            call_cmd('systemctl restart petasan-sync-replication-node')

        if cluster_config.get_node_info().is_iscsi or cluster_config.get_node_info().is_storage:
            logger.info("Starting petasan tuning service")
            call_cmd("systemctl restart petasan-tuning &")


    elif building_stage:

        call_cmd('systemctl start petasan-mount-sharedfs')
        if cluster_config.get_node_info().is_management:
            call_cmd('systemctl start petasan-cluster-leader')

        logger.info("Starting cluster file sync service")
        call_cmd('systemctl start petasan-file-sync')

        # replace node
        if cluster_config.get_node_info().is_backup:
            logger.info("Replace cluster node sync service")
            call_cmd('systemctl start petasan-sync-replication-node')
        # end

        call_cmd('/opt/petasan/scripts/load_iscsi_mods.sh')
        if cluster_config.get_node_info().is_iscsi:
            logger.info("Starting PetaSAN service")
            call_cmd('systemctl start petasan-iscsi')
            sleep(2)

        if cluster_config.get_node_info().is_management:
            logger.info("Starting Cluster Management application")
            call_cmd('systemctl start petasan-admin')

        # activate PetaSAN custom vgs
        cm = CacheManager()
        cm.activate()

        # remove any unused ceph-volume services
        ceph_disk_lib.delete_unused_ceph_volume_services()

        logger.info("Starting Node Stats Service")
        call_cmd('systemctl start petasan-node-stats')

        logger.info("Starting OSDs")
        call_cmd('systemctl restart petasan-start-osds')

        if cluster_config.get_node_info().is_iscsi or cluster_config.get_node_info().is_storage:
            logger.info("Starting petasan tuning service")
            call_cmd("systemctl restart petasan-tuning &")



    elif not building_stage and not cluster_complete:
        logger.info("Start settings IPs")
        call_cmd('python ' + ConfigAPI().get_node_start_ips_script_path())


cluster_config = configuration()
building_stage = False

if len(sys.argv) > 1:
    if str(sys.argv[1]) == 'build':
        building_stage = True

startup_services(building_stage, cluster_config.are_all_mgt_nodes_in_cluster_config())

