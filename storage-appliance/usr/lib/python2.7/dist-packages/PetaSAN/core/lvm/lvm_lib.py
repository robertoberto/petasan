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

from ceph_volume.api import lvm
from PetaSAN.core.common.cmd import *
from PetaSAN.core.common.log import logger
import json


# Activate logical volume group :
#################################
def activate_vg(vg_name):
    """
    Activating Volume Group ...
    """
    cmd = "vgchange -a y {}".format(vg_name)
    ret, stdout, stderr = exec_command_ex(cmd)
    if ret != 0:
        if stderr:
            logger.error("lvm_lib : Error activating volume group --> {}".format(stderr))
            return None


# Create logical volume :
#########################
def create_lv(lv_name, vg_name, device_name):
    """
    Create a Logical Volume in a Volume Group. Command looks like :
        lvcreate -l 100%FREE -n lv_name vg_name device_name

    :param lv_name: The name of the LV
    :param vg_name: The name of the VG
    :param device_name: The name of the device
    """
    # size : in GB , it will take 100% free space of disk
    cmd = "lvcreate -l 100%FREE -n {} {} {}".format(lv_name, vg_name, device_name)
    ret, stdout, stderr = exec_command_ex(cmd)
    if ret != 0:
        if stderr:
            logger.error("lvm_lib : Error creating logical volume --> {}".format(stderr))
            return None
    return lv_name


# Create Physical Volume :
##########################
def create_pv(partition_name):
    """
    Create a physical volume from a device or partition ...
    """
    # lvm.create_pv(partition_name)
    cmd = "pvcreate "
    cmd = cmd + "-v "     # verbose
    cmd = cmd + "-f "     # force it
    cmd = cmd + "--yes "  # answer yes to any prompts
    cmd = cmd + partition_name
    ret, stdout, stderr = exec_command_ex(cmd)
    if ret != 0:
        if stderr:
            logger.error("lvm_lib : Error creating physical volume --> {}".format(stderr))
            return None

    return True


# Create Volume Group :
#######################
def create_vg(devices, vg_name):
    """
    Create a Volume Group. Command looks like :
        vgcreate --force --yes group_name device

    Once created the volume group is returned as a ``VolumeGroup`` object

    :param devices: A list of devices to create a VG. Optionally, a single
                    device (as a string) can be used.
    :param vg_name: The name of the VG
    """
    # vg = lvm.create_vg(devices, vg_name)
    cmd = "vgcreate --force --yes "
    cmd = cmd + vg_name

    for device in devices:
        cmd = cmd + " " + device

    ret, stdout, stderr = exec_command_ex(cmd)
    if ret != 0:
        if stderr:
            logger.error("lvm_lib : Error creating volume group --> {}".format(stderr))
            return None

    vg = get_vg(vg_name)
    return vg


# Deactivate logical volume group :
###################################
def deactivate_vg(vg_name):
    """
    Deactivating Volume Group ...
    """
    cmd = "vgchange -a n {}".format(vg_name)
    logger.info("Starting : {} ".format(cmd))
    ret, stdout, stderr = exec_command_ex(cmd)
    if ret != 0:
        if stderr:
            logger.error("lvm_lib : Error deactivating volume group --> {}".format(stderr))
            return None


# Get all available logical volumes :
#####################################
def get_api_lvs():
    """
    Return the list of logical volumes available in the system ...
    """
    lvs = lvm.get_api_lvs()
    return lvs


# Get physical disks by volume group name :
###########################################
def get_physical_disks(vg_name):
    main_devices = set()
    writecache_devices = set()
    dmcache_devices = set()
    is_writecache = False
    is_cache = False
    physical_disks = {}

    cmd = "lvs --reportformat json -a -o name,origin,segtype,devices,vg_name -v {}".format(vg_name)
    ret, out, stderr = exec_command_ex(cmd)
    if ret != 0 and stderr:
        logger.error(stderr)

    out_dict = json.loads(out)
    lvs_list = out_dict['report'][0]['lv']

    if len(out_dict['report']) > 0 and len(lvs_list) > 0:
        for i in range(len(lvs_list)):
            cache_type = lvs_list[i]['segtype']

            # this lv_name is used for : dm-writecache
            if cache_type == "writecache":
                is_writecache = True
                break
            # this lv_name is used for: dm-cache
            elif cache_type == "cache":
                is_cache = True
                break

        for i in range(len(lvs_list)):
            lv_name = lvs_list[i]['lv_name']
            origin = lvs_list[i]['origin']
            devices = lvs_list[i]['devices']
            dev_list = devices.split(",")

            if origin == "":
                # check if physical disks
                if devices.startswith("/dev/"):
                    for dev in dev_list:
                        # get PetaSAN cache disk
                        if lv_name == "[cache]" and is_writecache:
                            writecache_devices.add(dev.split("(")[0])
                        elif lv_name == "[cache]" and is_cache:
                            dmcache_devices.add(dev.split("(")[0])
                        else:
                            # get PetaSAN disk without cache
                            main_devices.add(dev.split("(")[0])

        physical_disks["main"] = main_devices
        physical_disks["writecache"] = writecache_devices
        physical_disks["dmcache"] = dmcache_devices

    return physical_disks


# Get physical volume groups by origin disk name :
##################################################
def get_pvg_by_disk(origin_disk):
    pvg_list = []
    cmd = "pvs --reportformat json -o lv_name,pv_name,vg_name"
    ret, out, stderr = exec_command_ex(cmd)

    out_dict = json.loads(out)
    pv_list = out_dict['report'][0]['pv']

    if len(out_dict['report']) > 0 and len(pv_list) > 0:
        for pv in pv_list:
            if origin_disk in pv["pv_name"]:
                pvg_list.append(pv)
    return pvg_list


# Get Volume Group :
####################
def get_vg(vg_name):
    """
    Return a matching vg for the current system ...
    :param vg_name: The name of the VG
    """
    vg = lvm.get_vg(vg_name)
    return vg


# Detect if a device is an LV or not :
######################################
def is_lv(device_name):
    """
    Boolean to detect if a device is an LV or not ...
    """
    dev_name = "/dev/" + device_name
    is_logical_volume = False
    lvs = lvm.get_api_lvs()

    if lvs is not None:
        for lv in lvs:
            if lv["lv_path"] == dev_name:
                is_logical_volume = True
                break
    return is_logical_volume


# Rename Volume Group :
#######################
def rename_vg(old_name, new_name):
    """
    Renaming VG ...
    """
    cmd = "vgrename {} {}".format(old_name, new_name)
    ret, stdout, stderr = exec_command_ex(cmd)
    if ret != 0:
        if stderr:
            logger.error("lvm_lib : Error renaming volume group : {} to new name : {} --> {}".format(old_name,
                                                                                                     new_name,
                                                                                                     stderr))


# Get all volume groups :
#########################
def get_api_vgs():
    """
    Return the list of group volumes available in the system ...
    """
    vgs = lvm.get_api_vgs()
    return vgs


def get_vg_from_disk(origin_device):
    """
    # Get vg name (volume group) of the origin disk ...
    """
    pvg_list = get_pvg_by_disk(origin_device)

    if len(pvg_list) > 0:
        for item in pvg_list:
            if origin_device in item["pv_name"]:
                return item["vg_name"]