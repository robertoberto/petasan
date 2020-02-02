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

from PetaSAN.core.ceph.ceph_authenticator import CephAuthenticator
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.CustomException import CephException
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.common.log import logger


class Snapshots:
    def __init__(self):
        pass

    # Get all image names :
    def get_all_images(self, pool_name):
        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        images = []
        config = configuration()
        cluster_name = config.get_cluster_name()

        cmd = 'rbd ls {} {} --cluster {}'.format(pool_name, ceph_auth.get_authentication_string(),cluster_name)

        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            logger.error('General error in Ceph cmd : ' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        ls = stdout.splitlines()

        for image in ls:
            images.append(image)

        return images


    # Giving pool_name and image_name , get all image snapshots :
    def get_disk_snapshots(self, pool_name, image_name):
        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        image_snapshots = []
        config = configuration()
        cluster_name = config.get_cluster_name()

        cmd = 'rbd snap ls {}/{} {} --cluster {}'.format(pool_name, image_name, ceph_auth.get_authentication_string(), cluster_name)

        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            logger.error('General error in Ceph cmd : ' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        ls = stdout.splitlines()
        ls = ls[1:]

        for snapshot in ls:
            image_snapshots.append(self.get_snapshot_name(snapshot))

        return image_snapshots


    # Extract snapshot name from the giving line :
    def get_snapshot_name(self, line):
        words = line.split()
        snapshot_name = words[1]

        return snapshot_name


    # Giving pool_name , image_name and snapshot_name , create snapshot for the image :
    def create_snapshot(self, pool_name, image_name, snap_name):
        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        config = configuration()
        cluster_name = config.get_cluster_name()

        cmd = 'rbd snap create {}/{}@{} {} --cluster {}'.format(pool_name, image_name, snap_name, ceph_auth.get_authentication_string(),cluster_name)

        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            logger.error('General error in Ceph cmd : ' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        return True


    # Giving pool_name , image_name and snapshot_name , delete snapshot for the image :
    def delete_snapshot(self, pool_name, image_name, snap_name):
        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        config = configuration()
        cluster_name = config.get_cluster_name()
        cmd = 'rbd snap rm {}/{}@{} {} --cluster {}'.format(pool_name, image_name, snap_name, ceph_auth.get_authentication_string(), cluster_name)

        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            logger.error('General error in Ceph cmd : ' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        return True


    # Giving pool_name and image_name , delete all snapshots for the image :
    def delete_snapshots(self, pool_name, image_name):
        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        config = configuration()
        cluster_name = config.get_cluster_name()
        cmd = 'rbd snap purge {}/{} {} --cluster {}'.format(pool_name, image_name, ceph_auth.get_authentication_string(), cluster_name)

        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            logger.error('General error in Ceph cmd : ' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        return True


    # Giving pool_name , image_name and snapshot_name , rollback image to this snapshot :
    def rollback_to_snapshot(self, pool_name, image_name, snap_name):
        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        config = configuration()
        cluster_name = config.get_cluster_name()
        cmd = 'rbd snap rollback {}/{}@{} {} --cluster {}'.format(pool_name, image_name, snap_name, ceph_auth.get_authentication_string(), cluster_name)

        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            logger.error('General error in Ceph cmd : ' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        return True
