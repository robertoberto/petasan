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
from PetaSAN.backend.replication.manage_tmp_files import ManageTmpFile
from PetaSAN.core.common.CustomException import ReplicationException
from PetaSAN.core.common.RSAEncryption import RSAEncryption
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.common.log import logger


class ManageDestinationCluster:
    def __init__(self):
        pass

    # ##################################################################################################################
    def add_destination_cluster(self, destination_cluster):
        consul_api = ConsulAPI()
        # check if a destination cluster with the same name already exists and if so raise an exception
        dest_cluster = consul_api.get_replication_destination_cluster(destination_cluster.cluster_name)
        if dest_cluster:
            raise ReplicationException(ReplicationException.DESTINATION_CLUSTER_EXIST,
                                       "This destination cluster is already exist.")

        # validate destination cluster name

        # from PetaSAN.backend.replication.manage_remote_replication import ManageRemoteReplication
        # manage_remote_replication = ManageRemoteReplication()

        cluster_name =  self.get_dest_cluster_name(destination_cluster)
        if cluster_name != destination_cluster.cluster_name:
            raise ReplicationException(ReplicationException.WRONG_CLUSTER_NAME,
                                       "Wrong destination cluster name.")

        # add cluster fsid to the cluster entity
        # manage_remote_replication.cluster_name = destination_cluster.cluster_name

        destination_cluster.cluster_fsid = self.get_dest_cluster_fsid(destination_cluster)


        # encrypt the private key using RSA algorithm before saving in consul
        private_key = destination_cluster.ssh_private_key
        rsa_encrypt = RSAEncryption()
        pub_key = rsa_encrypt.get_key(rsa_encrypt.pub_key_path)
        encrypted_key = rsa_encrypt.encrypt_public(private_key, pub_key)
        destination_cluster.ssh_private_key = encrypted_key

        # save destination cluster entity in consul
        consul_api.update_replication_destination_cluster(destination_cluster)

    # ##################################################################################################################
    def delete_replication_dest_cluster(self, dest_cluster):
        consul_api = ConsulAPI()
        used_in_replication = 0

        # Get All Replication Jobs #
        consul_api = ConsulAPI()
        replication_jobs = consul_api.get_replication_jobs()

        for key, value in replication_jobs.iteritems():
            if value.destination_cluster_name == dest_cluster.cluster_name:
                used_in_replication += 1

        if used_in_replication > 0:
            raise ReplicationException(ReplicationException.DESTINATION_CLUSTER_USED_IN_REPLICATION,"This destination cluster is already used in replication job.")

        consul_api.delete_replication_destination_cluster(dest_cluster)

    # ##################################################################################################################
    def edit_destination_cluster(self, dest_cluster):
        consul_api = ConsulAPI()

        # encrypt the private key using RSA algorithm before saving in consul
        key_text = dest_cluster.ssh_private_key
        rsa_encrypt = RSAEncryption()
        pub_key = rsa_encrypt.get_key(rsa_encrypt.pub_key_path)
        encrypted_key = rsa_encrypt.encrypt_public(key_text, pub_key)
        dest_cluster.ssh_private_key = encrypted_key

        # save destination cluster entity in consul
        consul_api.update_replication_destination_cluster(dest_cluster)

    # ##################################################################################################################
    def get_replication_dest_cluster(self, cluster_name):
        consul_api = ConsulAPI()
        destination_cluster = consul_api.get_replication_destination_cluster(cluster_name)

        # ==========  Decrypt ssh private key  ========== #
        encrypted_key = destination_cluster.ssh_private_key
        rsa_decrypt = RSAEncryption()
        prv_key = rsa_decrypt.get_key(rsa_decrypt.prv_key_path)
        decrypted_key = rsa_decrypt.decrypt_private(encrypted_key, prv_key)

        # ==========  Update entity  ========== #
        destination_cluster.ssh_private_key = decrypted_key

        return destination_cluster

    # ##################################################################################################################
    def get_replication_dest_clusters(self):
        consul_api = ConsulAPI()
        dest_clusters_list = consul_api.get_replication_destination_clusters()

        for key, value in dest_clusters_list.iteritems():
            # ==========  Decrypt ssh private key  ========== #
            encrypted_key = value.ssh_private_key
            rsa_decrypt = RSAEncryption()
            prv_key = rsa_decrypt.get_key(rsa_decrypt.prv_key_path)
            decrypted_key = rsa_decrypt.decrypt_private(encrypted_key, prv_key)

            # ==========  Update entity  ========== #
            value.ssh_private_key = decrypted_key
        return dest_clusters_list

    # ##################################################################################################################
    # def test_connection(self, dest_cluster):
    #     try:
    #         from PetaSAN.backend.replication.manage_remote_replication import ManageRemoteReplication
    #         manage_remote_rep = ManageRemoteReplication()
    #         disks_list = manage_remote_rep.get_replicated_disks_list()
    #         return True
    #     except:
    #         return False


        # manage_replication = ManageReplicationJobs()
        # replication_jobs = manage_replication.get_replication_jobs()
        # print(replication_jobs)
        # for key, value in replication_jobs.iteritems():
        #             print(value.destination_cluster_name)

    # ##################################################################################################################
    # Getting "Remote Cluster" fsid :
    def get_dest_cluster_name(self, dest_cluster):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
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
        parser_key = "dest-cluster-name"  # Define parser key

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {}"'.format(sshkey_path, dest_user_name, dest_cluster_ip,
                                                                           script_file, parser_key)

        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Destination Cluster | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Destination Cluster | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Destination Cluster | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Destination Cluster | Cannot get destination cluster name , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination cluster name ')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Destination Cluster | Cannot get destination cluster name.')
                raise Exception(str(stdout))

            else:
                logger.error('Manage Destination Cluster | Cannot get destination cluster name .')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination cluster name ')

        if stdout and ('Error' in stdout):
            logger.error('Manage Destination Cluster | Cannot get destination cluster name.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination cluster name ')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Destination Cluster | Cannot get destination cluster name , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination cluster name')

        stdout_json = json.loads(str(stdout))
        return stdout_json

    # ##################################################################################################################
    # Getting "Remote Cluster" fsid :
    def get_dest_cluster_fsid(self, dest_cluster):
        mng_file = ManageTmpFile()

        # Get destination cluster info #
        # ---------------------------- #
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
        parser_key = "cluster-fsid"  # Define parser key

        # Define cmd command
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {}"'.format(sshkey_path, dest_user_name, dest_cluster_ip,
                                                                           script_file, parser_key)

        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        # ------------------------- #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr):
                logger.error('Manage Destination Cluster | Connection timed out , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_TIMEOUT, 'Connection timed out')

            elif stderr and ('Connection refused' in stderr):
                logger.error('Manage Destination Cluster | Connection refused , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.CONNECTION_REFUSED, 'Connection refused')

            elif stderr and ('Permission denied' in stderr):
                logger.error('Manage Destination Cluster | Permission denied , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.PERMISSION_DENIED, 'Permission denied')

            elif stderr and ("warning" not in stderr.lower()):
                logger.error('Manage Destination Cluster | Cannot get destination cluster fsid , Error = ' + str(stderr))
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination cluster fsid')

            elif stdout and ('Error' in stdout):
                logger.error('Manage Destination Cluster | Cannot get destination cluster fsid.')
                raise Exception(str(stdout))

            else:
                logger.error('Manage Destination Cluster | Cannot get destination cluster fsid.')
                raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination cluster fsid')

        if stdout and ('Error' in stdout):
            logger.error('Manage Destination Cluster | Cannot get destination cluster fsid.')
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination cluster fsid')

        if stderr and ("warning" not in stderr.lower()):
            logger.error('Manage Destination Cluster | Cannot get destination cluster fsid , Error = ' + str(stderr))
            raise ReplicationException(ReplicationException.GENERAL_EXCEPTION, 'Cannot get destination cluster fsid')

        stdout_json = json.loads(str(stdout))
        return stdout_json

    # ##################################################################################################################
