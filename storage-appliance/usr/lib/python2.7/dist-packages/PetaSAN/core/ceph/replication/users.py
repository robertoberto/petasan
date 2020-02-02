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

import os
import time
from PetaSAN.core.common.CustomException import CephException, ReplicationException
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.common.log import logger
from PetaSAN.core.cluster.configuration import configuration
import subprocess
import json

class Users(object):

    def __init__(self):
        self.group = 'replicators'
        self.gid = 5500


    def add_replication_sys_user(self, user_name, user_id):
        cmd = "getent group {}".format(self.group)
        ret, out ,err  = exec_command_ex(cmd)
        if ret != 0:
            cmd2 = "groupadd -g {} {}".format (self.gid, self.group)
            ret2, out2 ,err2  = exec_command_ex(cmd2)
            if ret2 != 0 and err2:
                logger.error("Error Creating the {} group ".format(self.group))

        cmd3 = "useradd {} -s /bin/bash -md /home/{} -g {} -u {}".format(user_name , user_name, self.group, user_id)
        ret3, out3 ,err3  = exec_command_ex(cmd3)
        if ret3 != 0 and err3 and 'already exists' in err3:
            raise ReplicationException(ReplicationException.SYSTEM_USER_EXIST, 'ThisSystemUserAlreadyExists:')



    def is_ceph_user_exist(self, user_name):
        found = True
        cmd = "ceph auth get client.{}".format(user_name)
        ret, stdout ,stderr  = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                if "Error" in stderr:
                    found = False
        return found


    def add_ceph_user(self, user_name, pool_list):
        config = configuration()
        cluster_name = config.get_cluster_name()
        pool_string = ""
        if len(pool_list) > 0:
            for pool in pool_list:
                pool_string += "\'profile rbd pool=" + pool + "\',"
            if pool_string[-1] == ",":
                pool_string = pool_string[:-1]
        else:
            pool_string = "\'profile rbd\'"

        cmd = "ceph auth get-or-create client.{} mgr 'allow r' mon 'profile rbd' osd {} >> /etc/ceph/{}.client.{}.keyring  " \
              "--cluster {} ".format (user_name, pool_string, cluster_name, user_name, cluster_name)
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            if stderr:
                if 'Connection timed out' in stderr or 'error connecting' in stderr:
                    logger.error('Error in Ceph Connection cmd:' + cmd)
                    raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')



    def get_replication_sys_users(self):
        users_list = []
        cmd = 'cut -d: -f1 /etc/passwd | xargs groups | grep {}'.format(self.group)
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            return users_list
        out = stdout.split('\n')
        if len(out[-1]) == 0:
            del out[-1]
        for user in out:
            if user.split(':')[1].replace(" ", "") == self.group:
                user_name = user.split(':')[0].replace(" ", "")
                users_list.append(user_name)
        return users_list


    def delete_ceph_user(self, user_name):
        status = True
        config = configuration()
        cluster_name = config.get_cluster_name()

        cmd = "ceph auth del client.{} --cluster {}".format (user_name, cluster_name)
        ret, stdout ,stderr  = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                if 'does not exist' in stderr:
                    logger.error('Error in Ceph Connection cmd:' + cmd)
                    raise ReplicationException(ReplicationException.CEPH_USER_DOES_NOT_EXIST, 'UserNotExist')

                if 'Connection timed out' in stderr or 'error connecting' in stderr:
                    logger.error('Error in Ceph Connection cmd:' + cmd)
                    raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        keyring_file = "/etc/ceph/" + cluster_name + ".client." + user_name + ".keyring"

        if os.path.exists(keyring_file):
            os.remove(keyring_file)

        return status


    def delete_system_user(self, user_name):
        cmd = "userdel -r {}".format(user_name)
        ret, out ,err  = exec_command_ex(cmd)

        if ret != 0 and err:
            logger.error("error deleting system user")



    def generate_tmp_ssh_keys(self, pub_key_file, prv_key_file):
        if os.path.exists(prv_key_file):
            os.remove(prv_key_file)
            os.remove(pub_key_file)
        cmd = 'ssh-keygen -t rsa -N \"\" -f {}'.format(prv_key_file)

        if subprocess.call(cmd,shell=True) == 0:
            return True

        return False


    def generate_ssh_keys(self, user_name, overwrite):
        stat = False
        path = '/home/' + user_name +'/.ssh/'
        id_rsa_file = '/home/' + user_name +'/.ssh/id_rsa'
        id_rsa_pub_file = '/home/' + user_name +'/.ssh/id_rsa.pub'

        if not overwrite and os.path.exists(id_rsa_file):
            return
        elif overwrite and os.path.exists(id_rsa_file):
            os.remove(id_rsa_file)
            os.remove(id_rsa_pub_file)

        cmd = 'ssh-keygen -t rsa -N \"\" -f {}'.format(user_name, id_rsa_file)
        if subprocess.call(cmd,shell=True) ==0:
            stat = True
        else:
            logger.error("Error generating ssh keys")

        return stat


    def get_ceph_users(self):
        config = configuration()
        cluster_name = config.get_cluster_name()
        cmd = "ceph auth ls --format json --cluster {}".format(cluster_name)
        ret, stdout ,stderr  = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                if 'Connection timed out' in stderr or 'error connecting' in stderr:
                    logger.error('Error in Ceph Connection cmd:' + cmd)
                    raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')


        users = json.loads(stdout)

        return users['auth_dump']


    def get_current_system_user(self):
        try:
            cmd = "id -u -n "
            ret, out ,err  = exec_command_ex(cmd)

            return out

        except Exception as e:
            logger.error(e)


    def get_ssh_prv_key(self, user_name):
        path = '/home/' + user_name +'/.ssh/id_rsa'
        id_rsa_file = os.path.expanduser(path)
        private_key = ""
        try:
            if os.path.exists(id_rsa_file):
                with open(id_rsa_file, 'r') as outfile:
                    private_key = outfile.read()
        except Exception as e:
            logger.error(e)

        return private_key


    def is_system_user_exist(self, user_name):
        found = True
        cmd = "getent passwd {}".format(user_name)
        ret, out, err  = exec_command_ex(cmd)
        if len(out) == 0:
            found = False

        return found


    def test_connection(self):
        pass


    def set_authorized_key(self, user_name):
        path = '/home/{}/.ssh/'.format(user_name)
        cmd = 'touch {}authorized_keys'.format(path)
        ret, out, err = exec_command_ex(cmd)

        cmd2 = 'cat {}id_rsa.pub >> {}authorized_keys'.format(path, path)
        ret2, out2, err2 = exec_command_ex(cmd2)


    def get_auth_pools(self, user_name):
        config = configuration()
        cluster_name = config.get_cluster_name()
        cmd = "ceph auth get client.{} --format json --cluster {}".format(user_name, cluster_name)
        ret, stdout ,stderr  = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                if 'Connection timed out' in stderr or 'error connecting' in stderr:
                    logger.error('Error in Ceph Connection cmd:' + cmd)
                    raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        user_info = json.loads(stdout)
        pools_info = user_info[0]['caps']['osd']
        auth_pools = []
        if 'profile rbd pool=' in pools_info:
            auth_pools_list = pools_info.replace('profile rbd pool=', "")
            if "," in auth_pools_list:
                auth_pools = auth_pools_list.split(',')
            else:
                auth_pools.append(auth_pools_list)

        return auth_pools


    def update_auth_pools(self, user_name, pool_list):
        config = configuration()
        cluster_name = config.get_cluster_name()
        pool_string = ""
        if len(pool_list) > 0:
            for pool in pool_list:
                pool_string += "\'profile rbd pool=" + pool + "\',"
            if pool_string[-1] == ",":
                pool_string = pool_string[:-1]
        else:
            pool_string = "\'profile rbd\'"

        cmd = "ceph auth caps client.{} mgr 'allow r' mon 'profile rbd' osd {} --cluster {}".format ( user_name , pool_string, cluster_name)
        ret, stdout ,stderr  = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                logger.error('failed to run cmd ' + cmd)
                return False

            return False

        return True




