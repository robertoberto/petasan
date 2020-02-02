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

from PetaSAN.backend.replication.manage_tmp_files import ManageTmpFile
from PetaSAN.core.common.RSAEncryption import RSAEncryption
from PetaSAN.core.entity.models.replication_user import ReplicationUser
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.common.CustomException import ReplicationException
from PetaSAN.backend.manage_node import ManageNode
from PetaSAN.core.ceph.replication.users import Users
import os
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.common.log import logger


class ManageUsers(object):

    def __init__(self):
        pass


    def get_replication_users(self):
        users_list = ConsulAPI().get_replication_users()
        return users_list


    def add_user(self, user_name, auth_pools):
        backup_nodes_list = []
        nodes_list = ManageNode().get_node_list()
        for node_info in nodes_list:
            if node_info.is_backup:
                backup_nodes_list.append(node_info.name)

        user_info = ConsulAPI().get_replication_user(user_name)
        if user_info and len(user_info.user_name) > 0:
            raise ReplicationException(ReplicationException.SYSTEM_USER_EXIST, 'ThisSystemUserAlreadyExistsInNodes:{}'.format(backup_nodes_list))

        user = Users()
        ceph_usr_stat = user.is_ceph_user_exist(user_name)
        if ceph_usr_stat:
            raise ReplicationException(ReplicationException.CEPH_USER_EXIST, 'ThisCephUserAlreadyExists')

        cluster_name = configuration().get_cluster_name()
        ceph_keyring_path = '/etc/ceph/{}.client.{}.keyring'.format(cluster_name, user_name)

        replication_user = ReplicationUser()
        replication_user.user_name = user_name
        replication_user.auth_pools = auth_pools

        rsa_encrypt = RSAEncryption()
        rsa_pub_key = rsa_encrypt.get_key(rsa_encrypt.pub_key_path)


        user.add_ceph_user(user_name, auth_pools)

        ceph_keyring_value = self.get_file_content(ceph_keyring_path)
        enc_ceph_keyring = rsa_encrypt.encrypt_public(ceph_keyring_value, rsa_pub_key)
        replication_user.ceph_keyring = enc_ceph_keyring

        pub_file = ConfigAPI().get_replication_user_pubkey_file_path()
        prv_file = ConfigAPI().get_replication_user_prvkey_file_path()
        rep_path = ConfigAPI().get_replication_tmp_file_path()

        if not os.path.exists(rep_path):
            os.mkdir(rep_path)

        user.generate_tmp_ssh_keys(pub_file, prv_file)

        pub_key_value = self.get_file_content(pub_file)
        replication_user.ssh_pub_key = pub_key_value

        prv_key_value = self.get_file_content(prv_file)
        enc_prv_key = rsa_encrypt.encrypt_public(prv_key_value, rsa_pub_key)
        replication_user.ssh_prv_key = enc_prv_key

        mng_file = ManageTmpFile()
        mng_file.delete_tmp_file (pub_file)
        mng_file.delete_tmp_file (prv_file)

        consul = ConsulAPI()
        consul.update_replication_user(replication_user)

        for node in backup_nodes_list:
            stat = self.sync_users(node)
            if not stat:
                logger.error("error sync users on the node {}".format(node))


    def sync_users(self, node):
        status = ManageNode().sync_replication_node(node)
        return status


    def get_file_content(self, path):
        content = ""
        if os.path.exists(path):
            with open(path, 'r') as input_file:
                content = input_file.read()
        return content


    def delete_replication_user(self, user_name):
        user = Users()
        stat = user.delete_ceph_user(user_name)
        if stat:
            consul = ConsulAPI()
            consul.delete_replication_user(user_name)
            nodes_list = ManageNode().get_node_list()
            for node_info in nodes_list:
                if node_info.is_backup:
                    stat = self.sync_users(node_info.name)
            return True
        else:
            return False


    def reset_prv_key(self, user_name):
        replication_user = self.get_replication_user(user_name)
        prv_key_value = replication_user.ssh_prv_key
        user = Users()
        pub_file = ConfigAPI().get_replication_user_pubkey_file_path()
        prv_file = ConfigAPI().get_replication_user_prvkey_file_path()

        stat = user.generate_tmp_ssh_keys(pub_file, prv_file)

        if stat:
            pub_key_value = self.get_file_content(pub_file)
            prv_key_value = self.get_file_content(prv_file)

            rsa_encrypt = RSAEncryption()
            rsa_pub_key = rsa_encrypt.get_key(rsa_encrypt.pub_key_path)
            enc_prv_key = rsa_encrypt.encrypt_public(prv_key_value, rsa_pub_key)
            enc_ceph_keyring = rsa_encrypt.encrypt_public(replication_user.ceph_keyring, rsa_pub_key)

            replication_user.ssh_prv_key = enc_prv_key
            replication_user.ssh_pub_key = pub_key_value
            replication_user.ceph_keyring = enc_ceph_keyring

            result = ConsulAPI().update_replication_user(replication_user)

            if result:
                mng_file = ManageTmpFile()
                mng_file.delete_tmp_file(pub_file)
                mng_file.delete_tmp_file(prv_file)

            nodes_list = ManageNode().get_node_list()
            for node_info in nodes_list:
                if node_info.is_backup:
                    stat = self.sync_users(node_info.name)

        return prv_key_value


    def set_prv_key(self, user_name, private_key):
        path = '/home/' + user_name +'/.ssh/'
        file = 'id_rsa.pub'
        if not os.path.exists(path):
            os.makedirs(path)

        file = open(path + file, 'w')
        file.write(private_key)
        file.close()


    def update_auth_pools(self, user_name, auth_pools):
        user = Users()
        status = user.update_auth_pools(user_name, auth_pools)
        if status:
            replication_user = ConsulAPI().get_replication_user(user_name)
            replication_user.auth_pools = auth_pools
            ConsulAPI().update_replication_user(replication_user)
            nodes_list = ManageNode().get_node_list()
            for node_info in nodes_list:
                if node_info.is_backup:
                    stat = self.sync_users(node_info.name)
        return status


    def get_auth_pools(self, user_name):
        user = Users()
        auth_pools = user.get_auth_pools(user_name)
        return auth_pools


    def get_replication_user(self, user_name):
        user = ConsulAPI().get_replication_user(user_name)
        rsa_decrypt = RSAEncryption()
        prv_key = rsa_decrypt.get_key(rsa_decrypt.prv_key_path)
        decrypted_prv_key = rsa_decrypt.decrypt_private(user.ssh_prv_key, prv_key)
        user.ssh_prv_key = decrypted_prv_key
        decrypted_ceph_key = rsa_decrypt.decrypt_private(user.ceph_keyring, prv_key)
        user.ceph_keyring  = decrypted_ceph_key
        return user
