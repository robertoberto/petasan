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

import json
import os
from PetaSAN.backend.replication.manage_destination_cluster import ManageDestinationCluster
from PetaSAN.backend.replication.manage_tmp_files import ManageTmpFile
from PetaSAN.core.common.CustomException import ReplicationException, DiskListException, PoolException, CephException, \
    MetadataException

from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI


class ManageRemoteReplication:
    def __init__(self):
        self.cluster_name = ""
        self.node_name = ""
        self.pool_name = ""
        self.disk_id = ""
        self.snapshot_name = ""

    # ##################################################################################################################
    # Getting disk's metadata for "Remote Cluster" all disks on all pools (DiskMeta Objects):
    def get_disks_meta_list(self):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_script_path()
        parser_key = "disks-meta"  # Define parser key

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {}"'.format(sshkey_path, dest_user_name, dest_cluster_ip,
                                                         script_file, parser_key)
        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot get disks meta , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get disks meta')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot get disk meta.')
                out = str(stdout)

                # See which except has been raise in the script #
                # --------------------------------------------- #
                if 'PoolException' in stdout:
                    replaced_out = out.replace(' PoolException - ', ' ')
                    raise PoolException(PoolException.CANNOT_GET_POOL, replaced_out)

                if 'DiskListException' in stdout:
                    replaced_out = out.replace(' DiskListException - ', ' ')
                    raise DiskListException(DiskListException.DISK_NOT_FOUND, replaced_out)

                if 'CephException' in stdout:
                    replaced_out = out.replace(' CephException - ', ' ')
                    raise CephException(CephException.GENERAL_EXCEPTION, replaced_out)

                if 'MetadataException' in stdout:
                    replaced_out = out.replace(' MetadataException - ', ' ')
                    raise MetadataException(replaced_out)

                if 'Exception' in stdout:
                    replaced_out = out.replace(' Exception - ', ' ')
                    raise Exception(replaced_out)

                raise Exception(out)

            else:
                logger.error('Manage Remote Replication | Cannot get disks meta.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get disks meta')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot get disks meta.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get disks meta')

        if stdout and ('Exception' in stdout):
            logger.error('Manage Remote Replication | Cannot get disks meta.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get disks meta')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot get disks meta , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get disks meta')

        stdout_json = json.loads(str(stdout))
        return stdout_json

    # ##################################################################################################################
    # Getting disk's metadata for "Remote Cluster" replicated disks on all pools (DiskMeta Objects):
    @property
    def get_replicated_disks_list(self):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_script_path()
        parser_key = "replicated-disks-meta"  # Define parser key

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {}"'.format(sshkey_path, dest_user_name, dest_cluster_ip,
                                                                           script_file, parser_key)
        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot get replicated disks meta , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get replicated disks meta')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot get disk meta.')
                out = str(stdout)

                # See which except has been raise in the script #
                # --------------------------------------------- #
                if 'DiskListException' in stdout:
                    replaced_out = out.replace(' DiskListException - ', ' ')
                    raise DiskListException(DiskListException.DISK_NOT_FOUND, replaced_out)

                if 'CephException' in stdout:
                    replaced_out = out.replace(' CephException - ', ' ')
                    raise CephException(CephException.GENERAL_EXCEPTION, replaced_out)

                if 'MetadataException' in stdout:
                    replaced_out = out.replace(' MetadataException - ', ' ')
                    raise MetadataException(replaced_out)

                if 'Exception' in stdout:
                    replaced_out = out.replace(' Exception - ', ' ')
                    raise Exception(replaced_out)

                raise Exception(out)

            else:
                logger.error('Manage Remote Replication | Cannot get replicated disks meta.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get replicated disks meta')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot get replicated disks meta.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get replicated disks meta')

        if stdout and ('Exception' in stdout):
            logger.error('Manage Remote Replication | Cannot get disks meta.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get disks meta')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot get replicated disks meta , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get replicated disks meta')

        stdout_json = json.loads(str(stdout))
        return stdout_json

    # ##################################################################################################################
    # Getting a specific disk metadata from "Remote Cluster" giving a disk_id (DiskMeta Objects):
    def get_disk_meta(self):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_script_path()
        parser_key = "disk-meta"  # Define parser key
        arg1 = "--disk_id"

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} {} {}"'.format(sshkey_path, dest_user_name,
                                                                                 dest_cluster_ip, script_file,
                                                                                 parser_key, arg1, self.disk_id)

        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection refused')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot get disk meta , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get disk meta')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot get disk meta.')
                out = str(stdout)

                # See which except has been raise in the script #
                # --------------------------------------------- #
                if 'PoolException' in stdout:
                    replaced_out = out.replace(' PoolException - ', ' ')
                    raise PoolException(PoolException.CANNOT_GET_POOL, replaced_out)

                if 'DiskListException' in stdout:
                    replaced_out = out.replace(' DiskListException - ', ' ')
                    raise DiskListException(DiskListException.DISK_NOT_FOUND, replaced_out)

                if 'CephException' in stdout:
                    replaced_out = out.replace(' CephException - ', ' ')
                    raise CephException(CephException.GENERAL_EXCEPTION, replaced_out)

                if 'MetadataException' in stdout:
                    replaced_out = out.replace(' MetadataException - ', ' ')
                    raise MetadataException(replaced_out)

                if 'Exception' in stdout:
                    replaced_out = out.replace(' Exception - ', ' ')
                    raise Exception(replaced_out)

                raise Exception(out)

            else:
                logger.error('Manage Remote Replication | Cannot get disk meta.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get disk meta')


        if stdout and ('Exception' in stdout):
            logger.error('Manage Remote Replication | Cannot get disk meta.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get disk meta')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot get disk meta , Error = ' + str(stderr))
            raise DiskListException(DiskListException.DISK_NOT_FOUND, 'Cannot get disk meta')

        stdout_json = json.loads(str(stdout))
        return stdout_json

    # ##################################################################################################################
    # Giving the dictionary of 'replication_info' attribute , update 'replication_info' of "Remote Cluster" disk :
    def update_replication_info(self, replication_info):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_script_path()
        parser_key = 'update-replication-info'

        src_disk_id = replication_info['src_disk_id']
        src_disk_name = replication_info['src_disk_name']
        src_cluster_name = replication_info['src_cluster_name']
        src_cluster_fsid = replication_info['src_cluster_fsid']
        dest_disk_id = replication_info['dest_disk_id']
        dest_disk_name = replication_info['dest_disk_name']
        dest_cluster_name = replication_info['dest_cluster_name']
        dest_cluster_fsid = replication_info['dest_cluster_fsid']
        dest_cluster_ip = replication_info['dest_cluster_ip']

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} --disk_id {} --src_disk_id {} --src_disk_name \'{}\' --src_cluster_name \'{}\' --src_cluster_fsid {} --dest_disk_id {} --dest_disk_name \'{}\' --dest_cluster_name \'{}\' --dest_cluster_fsid {} --dest_cluster_ip {}"'.format(
            sshkey_path, dest_user_name, dest_cluster_ip,
            script_file, parser_key,
            self.disk_id,
            src_disk_id,
            src_disk_name,
            src_cluster_name,
            src_cluster_fsid,
            dest_disk_id,
            dest_disk_name,
            dest_cluster_name,
            dest_cluster_fsid,
            dest_cluster_ip)

        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot update replication info , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot update replication info')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot update replication info.')
                raise Exception(str(stdout))

            else:
                logger.error('Manage Remote Replication | Cannot update replication info.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot update replication info')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot update replication info.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot update replication info')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot update replication info , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot update replication info')

        # stdout_json = json.loads(str(stdout))
        return stdout

    # ##################################################################################################################
    # Delete 'replication_info' of "Remote Cluster" disk :
    def delete_replication_info(self):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_script_path()
        parser_key = 'delete-replication-info'

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} --disk_id {}"'.format(sshkey_path, dest_user_name,
                                                                                   dest_cluster_ip, script_file,
                                                                                   parser_key, self.disk_id)

        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot delete replication info , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete replication info')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot delete replication info.')
                raise Exception(str(stdout))

            else:
                logger.error('Manage Remote Replication | Cannot delete replication info.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete replication info')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot delete replication info.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete replication info')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot delete replication info , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete replication info')

        return stdout

    # # ##################################################################################################################
    def delete_dest_file(self, file_name):
        # Get destination cluster info #
        # ---------------------------- #
        mng_file = ManageTmpFile()

        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "rm -f {}"'.format(sshkey_path, dest_user_name,
                                                                                            dest_cluster_ip, file_name)

        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot delete file , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete file')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot delete file.')
                raise Exception(str(stdout))

            else:
                logger.error('Manage Remote Replication | Cannot delete file.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete file')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot delete file.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete file')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot delete file , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete file')

        return stdout

    def read_dest_file(self, file_name):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "cat {}"'.format(sshkey_path, dest_user_name,
                                                                            dest_cluster_ip, file_name)

        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot read file , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot read file')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot read file.')
                raise Exception(str(stdout))

            else:
                logger.error('Manage Remote Replication | Cannot read file.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot read file')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot read file.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot read file')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot read file , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot read file')

        return stdout

    # ##################################################################################################################
    def build_crontab(self):
        script_file = ConfigAPI().get_cron_script_path()  # Get the script file path
        parser_key = 'build'
        cmd = 'ssh -o StrictHostKeyChecking=no root@{} "{} {}"'.format(self.node_name, script_file, parser_key)

        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Error building crontab in node : {} , error : {}'.format(self.node_name ,stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Error building crontab')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Error building crontab in node : {} , error : {}'.format(self.node_name ,stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Error building crontab')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Error building crontab in node : {} , error : {}'.format(self.node_name ,stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Error building crontab')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Error building crontab in node : {}'.format(self.node_name))
                raise Exception(str(stdout))

            else:
                logger.error('Manage Remote Replication | Error building crontab in node : {}'.format(self.node_name))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Error building crontab')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Error building crontab in node : {} , error : {}'.format(self.node_name ,stdout))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Error building crontab')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Error building crontab in node : {} , error : {}'.format(self.node_name ,stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Error building crontab')

        return True

    # ##################################################################################################################
    # Giving disk_id of a "Remote Cluster" disk , get all image snapshots :
    def get_dest_snapshots(self):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_script_path()
        parser_key = "snapshot-list"
        arg1 = "--disk_id"

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} {} {}"'.format(sshkey_path, dest_user_name,
                                                                                 dest_cluster_ip, script_file,
                                                                                 parser_key , arg1, self.disk_id)

        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot get destination disk snapshots , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination disk snapshots')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot get disk meta.')
                out = str(stdout)

                # See which except has been raise in the script #
                # --------------------------------------------- #
                if 'CephException' in stdout:
                    replaced_out = out.replace(' CephException - ', ' ')
                    raise CephException(CephException.GENERAL_EXCEPTION, replaced_out)

                if 'Exception' in stdout:
                    replaced_out = out.replace(' Exception - ', ' ')
                    raise Exception(replaced_out)

                raise Exception(out)

            else:
                logger.error('Manage Remote Replication | Cannot get destination disk snapshots.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination disk snapshots')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot get destination disk snapshots.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination disk snapshots')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot get destination disk snapshots , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination disk snapshots')

        stdout_json = json.loads(str(stdout))
        return stdout_json

    # ##################################################################################################################
    # Giving disk_id and a snapshot_name of a "Remote Cluster" disk , delete the snapshot :
    def delete_dest_snapshot(self):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_script_path()
        parser_key = "delete-snapshot"

        arg1 = "--disk_id"
        arg2 = "--snapshot_name"

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} {} {} {} {}"'.format(sshkey_path, dest_user_name,
                                                                                       dest_cluster_ip, script_file,
                                                                                       parser_key , arg1,
                                                                                       self.disk_id, arg2,
                                                                                       self.snapshot_name)
        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot delete destination disk snapshot , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete destination disk snapshot')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot delete destination disk snapshot.')
                out = str(stdout)

                # See which except has been raise in the script #
                # --------------------------------------------- #
                if 'CephException' in stdout:
                    replaced_out = out.replace(' CephException - ', ' ')
                    raise CephException(CephException.GENERAL_EXCEPTION, replaced_out)

                if 'Exception' in stdout:
                    replaced_out = out.replace(' Exception - ', ' ')
                    raise Exception(replaced_out)

                raise Exception(out)

            else:
                logger.error('Manage Remote Replication | Cannot delete destination disk snapshot.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete destination disk snapshot')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot delete destination disk snapshot.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete destination disk snapshot')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot delete destination disk snapshot , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete destination disk snapshot')

        return stdout

    # ##################################################################################################################
    # Giving disk_id of a "Remote Cluster" disk , delete all snapshots of this image :
    def delete_dest_snapshots(self):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_script_path()
        parser_key = "delete-snapshots"

        arg1 = "--disk_id"

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} {} {}"'.format(sshkey_path, dest_user_name,
                                                                                 dest_cluster_ip, script_file,
                                                                                 parser_key , arg1, self.disk_id)
        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot delete destination disk snapshots , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete destination disk snapshots')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot delete destination disk snapshots.')
                out = str(stdout)

                # See which except has been raise in the script #
                # --------------------------------------------- #
                if 'CephException' in stdout:
                    replaced_out = out.replace(' CephException - ', ' ')
                    raise CephException(CephException.GENERAL_EXCEPTION, replaced_out)

                if 'Exception' in stdout:
                    replaced_out = out.replace(' Exception - ', ' ')
                    raise Exception(replaced_out)

                raise Exception(out)

            else:
                logger.error('Manage Remote Replication | Cannot delete destination disk snapshots.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete destination disk snapshots')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot delete destination disk snapshots.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete destination disk snapshots')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot delete destination disk snapshots , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot delete destination disk snapshots')

        return stdout

    # ##################################################################################################################
    # Giving disk_id and a snapshot_name of a "Remote Cluster" disk , rollback image to the snapshot :
    def rollback_dest_snapshot(self):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_script_path()
        parser_key = "rollback-snapshot"

        arg1 = "--disk_id"
        arg2 = "--snapshot_name"

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} {} {} {} {}"'.format(sshkey_path, dest_user_name,
                                                                                       dest_cluster_ip, script_file,
                                                                                       parser_key, arg1, self.disk_id,
                                                                                       arg2, self.snapshot_name)
        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot rollback destination disk to snapshot , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot rollback destination disk to snapshot')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot rollback destination disk to snapshot.')
                out = str(stdout)

                # See which except has been raise in the script #
                # --------------------------------------------- #
                if 'CephException' in stdout:
                    replaced_out = out.replace(' CephException - ', ' ')
                    raise CephException(CephException.GENERAL_EXCEPTION, replaced_out)

                if 'Exception' in stdout:
                    replaced_out = out.replace(' Exception - ', ' ')
                    raise Exception(replaced_out)

                raise Exception(out)

            else:
                logger.error('Manage Remote Replication | Cannot rollback destination disk to snapshot.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot rollback destination disk to snapshot')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot rollback destination disk to snapshot.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot rollback destination disk to snapshot')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot rollback destination disk to snapshot , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot rollback destination disk to snapshot')

        return stdout

    # ##################################################################################################################
    # Giving disk_id of a "Remote Cluster" disk , clear the disk :
    def clear_disk(self):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_clear_disk_script_path()
        arg1 = "--disk_id"
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} {}"'.format(sshkey_path, dest_user_name,
                                                                              dest_cluster_ip, script_file, arg1,
                                                                              self.disk_id)

        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Cannot run clear disk script at destination cluster , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot run clear disk script at destination cluster')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Cannot run clear disk script at destination cluster.')
                raise Exception(str(stdout))

            else:
                logger.error('Manage Remote Replication | Cannot run clear disk script at destination cluster.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot run clear disk script at destination cluster')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Cannot run clear disk script at destination cluster.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot run clear disk script at destination cluster')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Cannot run clear disk script at destination cluster , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot run clear disk script at destination cluster')

        return stdout


    # ##################################################################################################################
    # Check if : "/opt/petasan/config/replication/" path exists :
    def check_replication_folder(self):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(self.cluster_name)
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        # ----------------------------- #
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        # -------------------------------- #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster as follows #
        # ----------------------------------------------------- #
        script_file = ConfigAPI().get_replication_script_path()  # Get the script file path
        parser_key = "replication-folder-check"  # Define parser key

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {}"'.format(sshkey_path, dest_user_name, dest_cluster_ip,
                                                                           script_file, parser_key)
        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Remote Replication | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Remote Replication | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Remote Replication | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Remote Replication | Replication folder does not exist at destination cluster: ' + cmd + ' , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Replication folder does not exist at destination cluster')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Remote Replication | Replication folder does not exist at destination cluster.')
                raise Exception(str(stdout))

            else:
                logger.error('Manage Remote Replication | Replication folder does not exist at destination cluster.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Replication folder does not exist at destination cluster')

        if stdout and ('Error' in stdout):
            logger.error('Manage Remote Replication | Replication folder does not exist at destination cluster.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Replication folder does not exist at destination cluster')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Remote Replication | Replication folder does not exist at destination cluster , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Replication folder does not exist at destination cluster')

        return stdout

    # # ##################################################################################################################
