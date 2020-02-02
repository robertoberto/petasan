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
from PetaSAN.core.common.CustomException import PoolException
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.disk_info import DiskMeta


class CommandBuilder:
    def __init__(self):
        pass

    def build(self, job_entity, snapshot_ls, active_job_id, dest_cluster, sshkey_path):
        '''
        This function will form the command of RBD Replication
        '''
        ceph_api = CephAPI()

        source_disk_id = job_entity.source_disk_id
        source_disk_name = 'image-' + source_disk_id
        source_pool_name = ceph_api.get_pool_bydisk(source_disk_id)

        # If pool inactive #
        if source_pool_name is None:
            raise PoolException(PoolException.CANNOT_GET_POOL, "Cannot get pool of disk " + str(source_disk_id))

        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip

        destination_disk_id = job_entity.destination_disk_id
        destination_disk_name = 'image-' + destination_disk_id

        # Getting destination disk metadata ( to get the destination disk pool ) :
        from PetaSAN.backend.replication.manage_remote_replication import ManageRemoteReplication
        manage_remote_rep = ManageRemoteReplication()
        manage_remote_rep.cluster_name = job_entity.destination_cluster_name
        manage_remote_rep.disk_id = job_entity.destination_disk_id

        dest_meta_dict = manage_remote_rep.get_disk_meta()
        dest_disk_meta_obj = DiskMeta(dest_meta_dict)

        destination_pool_name = dest_disk_meta_obj.pool

        compression_algorithm = job_entity.compression_algorithm

        # Getting paths of "md5" and "progress" files #
        config_api = ConfigAPI()
        md5_1_path = config_api.get_replication_md5_1_file_path(active_job_id)
        md5_2_path = config_api.get_replication_md5_2_file_path(active_job_id)

        replication_progress_comp_file_path = config_api.get_replication_progress_comp_file_path(active_job_id)
        replication_progress_upcomp_file_path = config_api.get_replication_progress_uncomp_file_path(active_job_id)
        replication_progress_import_file_path = config_api.get_replication_progress_import_file_path(active_job_id)

        # Getting "pipe_reader" script path #
        script_file = ConfigAPI().get_replication_pipe_reader_script_path()

        auth_string = " -n client." + dest_user_name + " --keyring=/etc/ceph/ceph.client." + dest_user_name + ".keyring"

        # Building Command :
        # ==================
        cmd = 'rbd export-diff '

        if len(snapshot_ls) == 1:
            cmd = cmd + source_pool_name + '/' + source_disk_name + '@' + snapshot_ls[0]
        else:
            cmd = cmd + '--from-snap ' + snapshot_ls[0] + ' ' + source_pool_name + '/' + source_disk_name + '@' + snapshot_ls[1]

        cmd = cmd + ' - | tee >(md5sum | cut -d \' \' -f 1 > ' + md5_1_path + ') | ' + script_file + ' ' + replication_progress_upcomp_file_path + ' | '

        if len(compression_algorithm) > 0:
            cmd = cmd + compression_algorithm + ' | ' + script_file + ' ' + replication_progress_comp_file_path + ' | '

        cmd = cmd + 'ssh -o StrictHostKeyChecking=no -i ' + sshkey_path + ' ' + dest_user_name + '@' + dest_cluster_ip + ' "'

        if len(compression_algorithm) > 0:
            cmd = cmd + compression_algorithm + ' -d | '

        cmd = cmd + 'tee >(md5sum | cut -d \' \' -f 1 > ' + md5_2_path + ') | rbd import-diff - ' + destination_pool_name + '/' + destination_disk_name + auth_string + '"' + ' 2> ' + replication_progress_import_file_path

        return cmd

# ----------------------------------------------------------------------------------------------------------------------