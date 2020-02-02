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

from time import sleep
from PetaSAN.core.ceph import ceph_disk
from PetaSAN.core.common.cmd import *
from PetaSAN.core.common.log import logger
from PetaSAN.core.lvm.lvm_lib import *


class Zapper:

    def __init__(self):
        pass

    def zap_partition(self, partition_name):
        """
        Device example: /dev/sda1
        Requirements: Must be a partition.
        """
        partition_path = "/dev/" + partition_name
        cmd = 'umount ' + partition_path
        logger.info('Executing : ' + cmd)
        if not call_cmd_2(cmd):
            logger.error('Error executing : ' + cmd)

        # Removes the filesystem from a partition :
        cmd = 'wipefs --all ' + partition_path
        logger.info('Executing : ' + cmd)
        if not call_cmd_2(cmd):
            logger.error('Error executing : ' + cmd)
            return False

        #  Clears all data from the given path. Path should be an absolute path to partition.
        #  100MB of data is written to the path to make sure that
        #  there is no trace left of any previous Filesystem :
        cmd = 'dd if=/dev/zero of={} bs=1M count=20 oflag=direct,dsync >/dev/null 2>&1'.format(partition_path)
        logger.info('Executing : ' + cmd)
        if not call_cmd_2(cmd):
            logger.error('Error executing : ' + cmd)

        return True

    def zap_disk(self, disk_name):
        """
        Any whole (raw) device passed in as input will be zapped here.
        Device example: /dev/sda
        Requirements: None.
        """
        for device in ceph_disk.list_devices():
            device_path = device['path']
            name = ceph_disk.get_dev_name(device_path)

            if name != disk_name:
                continue

            if 'partitions' in device:
                for partition in device['partitions']:
                    if 'mount' in partition:
                        mount_path = partition['mount']

                        if mount_path is not None and 0 < len(mount_path):
                            cmd = 'umount ' + mount_path
                            logger.info('Executing : ' + cmd)
                            if not call_cmd_2(cmd):
                                logger.error('Error executing : ' + cmd)

                    if 'path' in partition:
                        partition_path = partition['path']
                        if partition_path is not None and 0 < len(partition_path):
                            sleep(3)

                            # Removes the filesystem from a partition :
                            cmd = 'wipefs --all ' + partition_path
                            logger.info('Executing : ' + cmd)
                            if not call_cmd_2(cmd):
                                logger.error('Error executing : ' + cmd)
                                return False

                            #  Clears all data from the given path. Path should be an absolute path to partition.
                            #  100MB of data is written to the path to make sure that
                            #  there is no trace left of any previous Filesystem :
                            cmd = 'dd if=/dev/zero of={} bs=1M count=20 oflag=direct,dsync >/dev/null 2>&1'.format(
                                partition_path)
                            logger.info('Executing : ' + cmd)
                            if not call_cmd_2(cmd):
                                logger.error('Error executing : ' + cmd)

        # Removes the filesystem from any passed device :
        cmd = 'wipefs --all ' + '/dev/' + disk_name
        logger.info('Executing : ' + cmd)
        if not call_cmd_2(cmd):
            logger.error('Error executing : ' + cmd)
            return False

        #  Clears all data from any passed device.
        #  500MB of data is written to the path to make sure that there is no trace left of any previous Filesystem :
        cmd = 'dd if=/dev/zero of=/dev/{} bs=1M count=20 oflag=direct,dsync >/dev/null 2>&1'.format(disk_name)
        logger.info('Executing : ' + cmd)
        if not call_cmd_2(cmd):
            logger.error('Error executing : ' + cmd)

        cmd = 'parted -s /dev/{} mklabel gpt'.format(disk_name)
        logger.info('Executing : ' + cmd)
        if not call_cmd_2(cmd):
            logger.error('Error executing : ' + cmd)

        cmd = 'partprobe ' + '/dev/' + disk_name
        logger.info('Executing : ' + cmd)
        if not call_cmd_2(cmd):
            logger.error('Error executing : ' + cmd)

        sleep(3)
        return True

    def clean(self, disk_name):
        # Check if a Volume Group (VG) is existed on the selected disk -->
        # in order to deactivate it first before cleaning the disk :
        # ----------------------------------------------------------------
        try:
            disk_vg = get_vg_from_disk(disk_name)
            if disk_vg is not None:
                deactivate_vg(disk_vg)

        except Exception as e:
            pass

        disk_path = "/dev/" + disk_name
        if ceph_disk.is_partition(disk_path):
            return self.zap_partition(disk_name)
        else:
            return self.zap_disk(disk_name)

