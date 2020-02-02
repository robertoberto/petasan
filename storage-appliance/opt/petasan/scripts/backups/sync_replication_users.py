#! /usr/bin/python
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

from PetaSAN.core.common.CustomException import ReplicationException, RSAEncryptionException
from PetaSAN.core.common.RSAEncryption import RSAEncryption
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.consul.api import ConsulAPI
import sys
import os
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.ceph.replication.users import Users
from PetaSAN.core.common.log import logger
from PetaSAN.core.common.enums import Status
from PetaSAN.core.common.CustomException import ConsulException

def main():
    try:
        node_info = configuration().get_node_info()
        init_user_id = 5000

        if not node_info.is_backup:
            print("Error : This node not a backup")
            sys.exit(-1)

        # get all replication system users
        user_obj = Users()
        sys_users = user_obj.get_replication_sys_users()
        if sys_users and len(sys_users) > 0:
            for user in sys_users:
                user_obj.delete_system_user(user)

        # get all replication users from consul
        replication_users = ConsulAPI().get_replication_users()
        cluster_name = configuration().get_cluster_name()
        # get RSA prv key for decryption
        rsa_decrypt = RSAEncryption()
        prv_key = rsa_decrypt.get_key(rsa_decrypt.prv_key_path)

        for user_name, user_info in replication_users.iteritems():
            status = user_obj.is_system_user_exist(user_name)
            if status:
                continue
            # create user folders
            user_path = '/home/' + user_name
            if not os.path.exists(user_path):
                os.mkdir(user_path)
            ssh_path = user_path +'/.ssh/'
            if not os.path.exists(ssh_path):
                os.mkdir(ssh_path)
            file = 'id_rsa.pub'
            pub_file_path = ssh_path + file
            prv_file_path = pub_file_path.split('.pub')[0]
            ceph_keyring_file_path = '/etc/ceph/' + cluster_name +'.client.' + user_name + '.keyring'

            # add replication system user
            user_obj.add_replication_sys_user(user_name, init_user_id)
            init_user_id += 1

            # get pub , prv , and keyring from consul
            encrypted_prv_key = user_info.ssh_prv_key
            pub_key = user_info.ssh_pub_key
            encrypted_ceph_key = user_info.ceph_keyring

            # decrypt prv key and save it in file
            decrypted_prv_key = rsa_decrypt.decrypt_private(encrypted_prv_key, prv_key)
            with open(prv_file_path, 'w+') as prv_file:
                prv_file.write(decrypted_prv_key)
            # save pub key in file
            with open(pub_file_path, 'w+') as pub_file:
                pub_file.write(pub_key)

            # create authorized key
            user_obj.set_authorized_key(user_name)

            # change own and permission for private key
            cmd = "chown -R {} {}".format(user_name, user_path)
            ret, out, err = exec_command_ex(cmd)
            cmd = "chmod 600 {}".format(prv_file_path)
            ret, out ,err = exec_command_ex (cmd)

            # decrypt ceph keyring and save it in file
            decrypted_ceph_keying = rsa_decrypt.decrypt_private(encrypted_ceph_key, prv_key)
            with open(ceph_keyring_file_path, 'w+') as pub_file:
                pub_file.write(decrypted_ceph_keying)

            # change own and permission for ceph keyring
            cmd = "chown {} /etc/ceph/{}.client.{}.keyring".format(user_name, cluster_name, user_name)
            ret, out, err = exec_command_ex (cmd)
            cmd = "chmod 600 /etc/ceph/{}.client.{}.keyring".format(cluster_name, user_name)
            ret, out, err = exec_command_ex(cmd)

        sys.exit(0)

    except ConsulException as e:
        print("Error : Failed to get replication users from consul")
        logger.error(e)
        sys.exit(-1)
    except RSAEncryptionException as e:
        if e.id == RSAEncryptionException.GENERAL_EXCEPTION:
            print("Error : Failed to get RSA key")
        elif e.id == RSAEncryptionException.DECRYPTION_EXCEPTION:
            print("Error : Failed to decrypt keys")
        logger.error(e)
        sys.exit(-1)
    except ReplicationException as e:
        if e.id == ReplicationException.SYSTEM_USER_EXIST:
            print("Error : System user already exist")
            logger.error(e)
        sys.exit(-1)
    except Exception as e:
        print("Error : General Error in script")
        logger.error(e)
        sys.exit(-1)





if __name__ == '__main__':
    if len(sys.argv) == 1:
        main()
    else:
        sys.exit("Usage: [sync_replication_users.py]")











