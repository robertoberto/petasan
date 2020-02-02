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

from PetaSAN.backend.replication.manage_destination_cluster import ManageDestinationCluster
from PetaSAN.core.ceph.api import CephAPI


class ManageDiskReplicationInfo:
    def __init__(self):
        pass

    ####################################################################################################################
    # Giving disk metadata and the dictionary of 'replication_info' attribute , update 'replication_info' of this disk :
    def update_replication_info(self, disk_meta, replication_info):
        ceph_api = CephAPI()
        disk_meta.replication_info = replication_info
        confirm = ceph_api.update_disk_metadata(disk_meta)
        return confirm

    ####################################################################################################################
    # Giving disk metadata , clear 'replication_info' dictionary s:
    def delete_replication_info(self, disk_meta):
        ceph_api = CephAPI()
        disk_meta.replication_info = {}
        confirm = ceph_api.update_disk_metadata(disk_meta)
        return confirm

    ####################################################################################################################
    ##
    def set_replication_info(self,cluster_name, disk_meta):
        manage_destination_cluster = ManageDestinationCluster()
        dest_cluster = manage_destination_cluster.get_replication_dest_cluster(cluster_name)

        disk_meta.replication_info["dest_cluster_ip"] = dest_cluster.remote_ip
        disk_meta.replication_info["dest_cluster_fsid"] = dest_cluster.cluster_fsid

        return disk_meta