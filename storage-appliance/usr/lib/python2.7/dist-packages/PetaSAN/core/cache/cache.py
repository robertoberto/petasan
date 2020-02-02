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

from flask import json
import random

from PetaSAN.core.ceph.ceph_disk import get_partition_size
from PetaSAN.core.lvm.lvm_lib import *
from PetaSAN.core.common.cmd import *
from PetaSAN.core.common.enums import CacheType
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.ceph import ceph_disk_lib
from PetaSAN.core.ceph import ceph_disk as ceph_disk
from PetaSAN.core.common.log import logger             # This line should be after the line --> from PetaSAN.core.lvm.lvm_lib import *


class Cache(object):
    def __init__(self):
        self.origin_device = ""
        self.cache_device = ""
        self.main_device = ""
        self.type = ""

    def load_json(self, j):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=True, indent=4)
        return j

    def get_dict(self):
        return self.__dict__

    def create(self, origin_device, cache_device):
        """
        # Build caching between origin disk and cache disk ...
        """
        pass

    def activate(self):
        """
        # Activating cache ...
        """
        pass

    def delete(self, origin_device):
        """
        # Remove caching between origin disk and cache disk ...
        """
        pass

    def get_physical_devices(self, origin_device):
        """
        # Get physical devices that linked to the vg (volume group) of the origin disk ...
        """
        pass

    def get_vg_by_disk(self, origin_device):
        """
        # Get vg name (volume group) of the origin disk ...
        """
        pvg_list = get_pvg_by_disk(origin_device)

        if len(pvg_list) > 0:
            for item in pvg_list:
                if origin_device in item["pv_name"] and "ps-" in item["vg_name"]:     # and "[main_" in item["lv_name"]:
                    return item["vg_name"]

#  ##=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###  #


class WriteCache(Cache):
    def __init__(self):
        Cache.__init__(self)
        self.type = CacheType.dm_writecache

    def create(self, origin_device, cache_device):
        self.origin_device = origin_device
        self.cache_device = cache_device
        devices = []
        cluster_fsid = ceph_disk.get_fsid(configuration().get_cluster_name())

        logger.info("Getting the next OSD ID :")
        logger.info("-------------------------")

        next_osd_id = ceph_disk_lib.get_next_osd_id()
        if len(next_osd_id) == 0:
            logger.error("Can't get next OSD id.")
            return None

        logger.info("next_osd_id = {}\n".format(str(next_osd_id)))
        vg_name = "ps-" + cluster_fsid + "-wc-osd." + str(next_osd_id)
        logger.info("vg_name = {}\n".format(str(vg_name)))

        cache_lv_name = "cache"
        main_lv_name = "main"
        origin_part_name = ""
        cache_part = ""

        try:
            logger.info("==================================================")
            logger.info("=====          Building DM-Writecache        =====")
            logger.info("==================================================")

            # ======================================= Slow Device ======================================= #
            # (1) Zapping the slow disk device :
            # ----------------------------------
            logger.info("Step 1 : Preparing Slow Disk :")
            logger.info("------------------------------")

            # (2) Creating one partition for the slow disk ( with same size of disk size ) :
            # ------------------------------------------------------------------------------
            origin_part_num = ceph_disk.create_osd_partition(origin_device)
            origin_part = ceph_disk.get_partition_name(origin_device, origin_part_num)

            if origin_part is not None:
                origin_part_name = '/dev/' + origin_part
                devices.append(origin_part_name)
                logger.info("origin_part_name = {}".format(str(origin_part_name)))
                logger.info("done\n")

            else:
                logger.info("Creating partition for the slow disk has been failed.")
                ceph_disk_lib.clean_disk(origin_device)
                return None

            # ======================================= Fast Device ======================================= #
            # (4) Get available partition for cache disk :
            # --------------------------------------------
            logger.info("Step 2 : Preparing Fast Disk :")
            logger.info("------------------------------")
            avail_partitions_ls = ceph_disk_lib.get_partitions_by_type(cache_device, ceph_disk_lib.cache_avail_ptype)

            if len(avail_partitions_ls) > 0:
                # Sorting partitions list alphabetically :
                avail_partitions_ls.sort()

                cache_part = avail_partitions_ls[0]
                cache_part_path = '/dev/' + cache_part

                ceph_disk_lib.clean_disk(cache_part)

                # clean meta data super block
                self.clean_superblock(cache_part)

                devices.append(cache_part_path)
                logger.info("cache_part_path = {}".format(str(cache_part_path)))
                logger.info("done\n")


            else:
                logger.info("Getting available partition for cache disk has been failed.")
                ceph_disk_lib.clean_disk(origin_device)
                return None

            # ==================================== Physical Volumes ===================================== #
            # (6) Creating Physical Volumes (pvs) :
            # -------------------------------------
            logger.info("Step 3 : Creating Physical Volumes :")
            logger.info("------------------------------------")
            if create_pv(origin_part_name) is None:
                logger.info("Creating Physical Volume on {} has been failed.".format(origin_part_name))
                ceph_disk_lib.clean_disk(origin_device)
                return None

            if create_pv(cache_part_path) is None:
                logger.info("Creating Physical Volume on {} has been failed.".format(cache_part_path))
                ceph_disk_lib.clean_disk(origin_device)
                ceph_disk_lib.clean_disk(cache_part)
                ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
                return None

            logger.info("done\n")

            # ====================================== Volume Groups ====================================== #
            # (7) Creating Volume Groups (vgs) :
            # ----------------------------------
            logger.info("Step 4 : Creating Volume Group :")
            logger.info("--------------------------------")
            vg = get_vg(vg_name)

            while vg is not None:
                next_osd_id = ceph_disk_lib.get_next_osd_id()
                if len(next_osd_id) == 0:
                    logger.error("Can't get next OSD id.")
                    logger.error("Creating Volume Group has been failed.")
                    ceph_disk_lib.clean_disk(origin_device)
                    ceph_disk_lib.clean_disk(cache_part)
                    ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
                    return None

                logger.info("new next_osd_id = {}\n".format(str(next_osd_id)))
                vg_name = "ps-" + cluster_fsid + "-wc-osd." + str(next_osd_id)
                logger.info("new vg_name = {}\n".format(str(vg_name)))

                vg = get_vg(vg_name)

            vg = create_vg(devices, vg_name)

            if vg is None:
                logger.info("Creating Volume Group has been failed.")
                ceph_disk_lib.clean_disk(origin_device)
                ceph_disk_lib.clean_disk(cache_part)
                ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
                return None

            vg_name = vg.vg_name
            logger.info("vg_name = {}".format(str(vg_name)))
            logger.info("done\n")

            # ===================================== Logical Volumes ===================================== #
            # (8) Creating Logical Volumes (lvs) :
            # ------------------------------------
            logger.info("Step 5 : Creating Logical Volumes :")
            logger.info("-----------------------------------")
            main_lv_name = create_lv(main_lv_name, vg_name, origin_part_name)

            if main_lv_name is None:
                logger.info("Creating Logical Volume for main device has been failed.")
                activate_vg(vg_name)
                ceph_disk_lib.clean_disk(origin_device)
                ceph_disk_lib.clean_disk(cache_part)
                ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)

                return None

            logger.info("main_lv_name = {}".format(str(main_lv_name)))

            cache_lv_name = create_lv(cache_lv_name, vg_name, cache_part_path)

            if cache_lv_name is None:
                logger.info("Creating Logical Volume for cache device has been failed.")
                activate_vg(vg_name)
                ceph_disk_lib.clean_disk(origin_device)
                ceph_disk_lib.clean_disk(cache_part)
                ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
                return None

            logger.info("cache_lv_name = {}".format(str(cache_lv_name)))
            logger.info("done\n")

            # =================================== Building writecache =================================== #
            logger.info("Step 6 : Building dm-writecache :")
            logger.info("---------------------------------")
            error = 0
            cmd = "lvchange -a n " + vg_name + "/" + cache_lv_name
            ret, stdout, stderr = exec_command_ex(cmd)

            if ret != 0:
                if stderr:
                    logger.info("Error running the command : {} , the error msg :\n{}".format(cmd, stderr))
                    error += 1
            else:
                logger.info("cmd = {}  --->  done".format(str(cmd)))
                cmd = "modprobe dm-writecache"
                ret, stdout, stderr = exec_command_ex(cmd)

                if ret != 0:
                    if stderr:
                        logger.info("Error running the command : {} , the error msg :\n{}".format(cmd, stderr))
                        error += 1
                else:
                    logger.info("cmd = {}  --->  done".format(str(cmd)))
                    cmd = 'lvconvert --yes --type writecache --cachevol ' + cache_lv_name + \
                          " --cachesettings 'writeback_jobs=102400' " + vg_name + "/" + main_lv_name
                    ret, stdout, stderr = exec_command_ex(cmd)

                    if ret != 0:
                        if stderr:
                            logger.info("Error running the command : {} , the error msg :\n{}".format(cmd, stderr))
                            error += 1

            if error > 0:
                activate_vg(vg_name)
                ceph_disk_lib.clean_disk(origin_device)
                ceph_disk_lib.clean_disk(cache_part)

                ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
                logger.info("Create WriteCache : Building writecache has been failed.")
                return None

            logger.info("cmd = {}  --->  done".format(str(cmd)))
            ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_used_ptype)

            lv_path = vg_name + "/" + main_lv_name
            logger.info("lv_path = {}".format(str(lv_path)))

            logger.info("done")
            logger.info("==================================================")

            return lv_path, cache_part

        except Exception as ex:
            err = "Cannot build writecache for disk {} and cache partition {} , Exception is : {}".format(
                origin_device, cache_device, ex.message)
            logger.exception(err)
            ceph_disk_lib.clean_disk(origin_device)
            ceph_disk_lib.clean_disk(cache_part)
            ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
            logger.info("==================================================")

    def activate(self):
        cluster_fsid = ceph_disk.get_fsid(configuration().get_cluster_name())
        vg_name = "ps-" + cluster_fsid + "-wc"

        logger.info("Starting activating PetaSAN lvs")
        call_cmd("modprobe dm-writecache")

        all_lvs_dict = get_api_vgs()

        for vg in all_lvs_dict:
            if vg['vg_name'].startswith(vg_name):
                logger.info("Activating {}".format(vg['vg_name']))
                call_cmd("vgchange -a y {}".format(vg['vg_name']))
                logger.info("Setting writeback jobs number.")
                call_cmd('dmsetup message {}/main 0 writeback_jobs 102400'.format(vg['vg_name']))

    def get_physical_devices(self, origin_device):
        pass

    def delete(self, origin_device):
        vg_name = self.get_vg_by_disk(origin_device)
        deactivate_vg(vg_name)

    def get_superblock_sector(self, partition_size):
        block_size = 4096

        nr_blocks = partition_size / (4096 + (16 * 2))    # partition_size  =  (4096 x nr_blocks) + (32 x nr_blocks)
        metadata_size = (nr_blocks * 16)                  # The size of one block of metadata = 16 bytes

        offset_remainder = metadata_size % block_size
        if offset_remainder != 0:
            metadata_size = (metadata_size - offset_remainder) + block_size

        superblock_sector = (metadata_size // 512)        # The size of one sector = 512 bytes
        return superblock_sector

    def clean_superblock(self, partition_name):
        writes_MB = 20
        writes_bytes = writes_MB * 1024 * 1024
        partition_size = get_partition_size(partition_name)
        superblock_bytes = self.get_superblock_sector(partition_size) * 512

        # superblock_bytes - writes_bytes // 2  >>  start before superblock_bytes
        # to reassure that it will be completely wipe :
        seek_bytes = int(superblock_bytes - writes_bytes // 2)

        cmd = 'dd bs=1M seek={} if=/dev/zero of=/dev/{} count={} oflag=seek_bytes,direct,dsync >/dev/null 2>&1'.format(
            seek_bytes, partition_name, writes_MB)

        logger.info('Executing : ' + cmd)
        if not call_cmd_2(cmd):
            logger.error('Error executing : ' + cmd)

#  ##=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###  #


class DMCache(Cache):
    def __init__(self):
        Cache.__init__(self)
        self.type = CacheType.dm_cache

    def create(self, origin_device, cache_device):
        self.origin_device = origin_device
        self.cache_device = cache_device
        devices = []
        cluster_fsid = ceph_disk.get_fsid(configuration().get_cluster_name())

        logger.info("Getting the next OSD ID :")
        logger.info("-------------------------")

        next_osd_id = ceph_disk_lib.get_next_osd_id()
        if len(next_osd_id) == 0:
            logger.error("Can't get next OSD id.")
            return None

        logger.info("next_osd_id = {}\n".format(str(next_osd_id)))
        vg_name = "ps-" + cluster_fsid + "-dmc-osd." + str(next_osd_id)
        logger.info("vg_name = {}\n".format(str(vg_name)))

        cache_lv_name = "cache"
        main_lv_name = "main"
        origin_part_name = ""
        cache_part = ""

        try:
            logger.info("==================================================")
            logger.info("=====            Building DM-Cache           =====")
            logger.info("==================================================")

            # ======================================= Slow Device ======================================= #
            # (1) Zapping the slow disk device :
            # ----------------------------------
            logger.info("Step 1 : Preparing Slow Disk :")
            logger.info("------------------------------")

            # (2) Creating one partition for the slow disk ( with same size of disk size ) :
            # ------------------------------------------------------------------------------
            origin_part_num = ceph_disk.create_osd_partition(origin_device)
            origin_part = ceph_disk.get_partition_name(origin_device, origin_part_num)

            if origin_part is not None:
                origin_part_name = '/dev/' + origin_part
                devices.append(origin_part_name)
                logger.info("origin_part_name = {}".format(str(origin_part_name)))
                logger.info("done\n")

            else:
                logger.info("Creating partition for the slow disk has been failed.")
                ceph_disk_lib.clean_disk(origin_device)
                return None

            # ======================================= Fast Device ======================================= #
            # (4) Get available partition for cache disk :
            # --------------------------------------------
            logger.info("Step 2 : Preparing Fast Disk :")
            logger.info("------------------------------")
            avail_partitions_ls = ceph_disk_lib.get_partitions_by_type(cache_device, ceph_disk_lib.cache_avail_ptype)

            if len(avail_partitions_ls) > 0:
                # Sorting partitions list alphabetically :
                avail_partitions_ls.sort()

                cache_part = avail_partitions_ls[0]
                cache_part_path = '/dev/' + cache_part
                devices.append(cache_part_path)
                logger.info("cache_part_path = {}".format(str(cache_part_path)))
                logger.info("done\n")

            else:
                logger.info("Getting available partition for cache disk has been failed.")
                ceph_disk_lib.clean_disk(origin_device)
                return None

            # ==================================== Physical Volumes ===================================== #
            # (6) Creating Physical Volumes (pvs) :
            # -------------------------------------
            logger.info("Step 3 : Creating Physical Volumes :")
            logger.info("------------------------------------")
            if create_pv(origin_part_name) is None:
                logger.info("Creating Physical Volume on {} has been failed.".format(origin_part_name))
                ceph_disk_lib.clean_disk(origin_device)
                return None

            if create_pv(cache_part_path) is None:
                logger.info("Creating Physical Volume on {} has been failed.".format(cache_part_path))
                ceph_disk_lib.clean_disk(origin_device)
                ceph_disk_lib.clean_disk(cache_part)
                ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
                return None

            logger.info("done\n")

            # ====================================== Volume Groups ====================================== #
            # (7) Creating Volume Groups (vgs) :
            # ----------------------------------
            logger.info("Step 4 : Creating Volume Group :")
            logger.info("--------------------------------")
            vg = get_vg(vg_name)

            while vg is not None:
                next_osd_id = ceph_disk_lib.get_next_osd_id()
                if len(next_osd_id) == 0:
                    logger.error("Can't get next OSD id.")
                    logger.error("Creating Volume Group has been failed.")
                    ceph_disk_lib.clean_disk(origin_device)
                    ceph_disk_lib.clean_disk(cache_part)
                    ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
                    return None

                logger.info("new next_osd_id = {}\n".format(str(next_osd_id)))
                vg_name = "ps-" + cluster_fsid + "-dmc-osd." + str(next_osd_id)
                logger.info("new vg_name = {}\n".format(str(vg_name)))

                vg = get_vg(vg_name)

            vg = create_vg(devices, vg_name)

            if vg is None:
                logger.info("Creating Volume Group has been failed.")
                ceph_disk_lib.clean_disk(origin_device)
                ceph_disk_lib.clean_disk(cache_part)
                ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
                return None

            vg_name = vg.vg_name
            logger.info("vg_name = {}".format(str(vg_name)))
            logger.info("done\n")

            # ===================================== Logical Volumes ===================================== #
            # (8) Creating Logical Volumes (lvs) :
            # ------------------------------------
            logger.info("Step 5 : Creating Logical Volumes :")
            logger.info("-----------------------------------")
            main_lv_name = create_lv(main_lv_name, vg_name, origin_part_name)

            if main_lv_name is None:
                logger.info("Creating Logical Volume for main device has been failed.")
                activate_vg(vg_name)
                ceph_disk_lib.clean_disk(origin_device)
                ceph_disk_lib.clean_disk(cache_part)
                ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)

                return None

            logger.info("main_lv_name = {}".format(str(main_lv_name)))

            cache_lv_name = create_lv(cache_lv_name, vg_name, cache_part_path)

            if cache_lv_name is None:
                logger.info("Creating Logical Volume for cache device has been failed.")
                activate_vg(vg_name)
                ceph_disk_lib.clean_disk(origin_device)
                ceph_disk_lib.clean_disk(cache_part)
                ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
                return None

            logger.info("cache_lv_name = {}".format(str(cache_lv_name)))
            logger.info("done\n")

            # =================================== Building dmcache =================================== #
            logger.info("Step 6 : Building dm-cache :")
            logger.info("----------------------------")
            error = 0

            cmd = 'lvconvert --yes --type cache --cachevol ' + cache_lv_name + \
                  "  --cachemode writeback " + vg_name + "/" + main_lv_name
            logger.info("running {}".format(cmd))
            ret, stdout, stderr = exec_command_ex(cmd)

            if ret != 0:
                if stderr:
                    logger.info("Error running the command : {} , the error msg :\n{}".format(cmd, stderr))
                    error += 1

            if error > 0:
                activate_vg(vg_name)
                ceph_disk_lib.clean_disk(origin_device)
                ceph_disk_lib.clean_disk(cache_part)

                ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
                logger.info("Create DM-Cache : Building dm-cache has been failed.")
                return None

            logger.info("cmd = {}  --->  done".format(str(cmd)))
            ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_used_ptype)

            lv_path = vg_name + "/" + main_lv_name
            logger.info("lv_path = {}".format(str(lv_path)))

            logger.info("done")
            logger.info("==================================================")

            return lv_path, cache_part

        except Exception as ex:
            err = "Cannot build dm-cache for disk {} and cache partition {} , Exception is : {}".format(
                origin_device, cache_device, ex.message)
            logger.exception(err)
            ceph_disk_lib.clean_disk(origin_device)
            ceph_disk_lib.clean_disk(cache_part)
            ceph_disk_lib.set_partition_type(cache_part, ceph_disk_lib.cache_avail_ptype)
            logger.info("==================================================")

    def activate(self):
        cluster_fsid = ceph_disk.get_fsid(configuration().get_cluster_name())
        vg_name = "ps-" + cluster_fsid + "-dmc"

        logger.info("Starting activating PetaSAN lvs")
        call_cmd("modprobe dm-cache")

        all_lvs_dict = get_api_vgs()

        for vg in all_lvs_dict:
            if vg['vg_name'].startswith(vg_name):
                logger.info("Activating {}".format(vg['vg_name']))
                call_cmd("vgchange -a y {}".format(vg['vg_name']))

    def get_physical_devices(self, origin_device):
        pass

    def delete(self, origin_device):
        vg_name = self.get_vg_by_disk(origin_device)
        deactivate_vg(vg_name)

