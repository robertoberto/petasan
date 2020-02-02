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

# from ceph_disk import main as ceph_disk
import time
import uuid
import re
from flask import json
from PetaSAN.core.ceph import ceph_disk as ceph_disk
from PetaSAN.core.ceph import ceph_osd
from PetaSAN.core.ceph.ceph_disk import is_partition
from PetaSAN.core.ceph.zapper import Zapper
from PetaSAN.core.common.cmd import *
from PetaSAN.core.common.smart import Smart
from PetaSAN.core.common import disk_util
from PetaSAN.core.common.enums import DiskUsage, OsdStatus
from PetaSAN.core.cluster.job_manager import JobManager
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.job import JobType
from PetaSAN.core.entity.ph_disk import DiskInfo
from PetaSAN.core.entity.ceph_volume import CephVolumeInfo
from PetaSAN.core.lvm import lvm_lib

# ======================================================================
# OSD Partition UUID #
ptype_osd = ceph_disk.PTYPE['osd']
ptype_journal = ceph_disk.PTYPE['journal']
ptype_blockdb = '30cd0809-c2b2-499c-8879-2d6b78529876'
ptype_block = 'cafecafe-9b03-4f30-b4c6-b4b80ceff106'
journal_avail_ptype = '103af3d7-a019-4e56-bfe0-4d664b989f40'
CEPH_VOLUME_LOG_PATH = '/opt/petasan/log'

cache_used_ptype = ceph_disk.PTYPE['cache']
cache_avail_ptype = '5b3f01d6-70d6-421a-a101-4b3131a8d600'
# ======================================================================

def get_ceph_volumes_info():
    ceph_volumes_disks = {}
    cluster_fsid = ''
    vg_name = ""
    partitions_uuid = {}
    try:
        cluster_fsid = ceph_disk.get_fsid(configuration().get_cluster_name())
        partitions_uuid = ceph_disk.get_partitions_uuid()
    except Exception as e:
        logger.error(e)
        pass
    cmd = 'ceph-volume --log-path ' + CEPH_VOLUME_LOG_PATH + ' lvm list --format json'
    ret, stdout, stderr = exec_command_ex(cmd)
    if ret != 0:
        if stderr:
            logger.error(stderr)
    if len(stdout) > 0:
        ceph_volumes_info = json.loads(stdout)
        for osd_id, osd_info in ceph_volumes_info.iteritems():
            try:
                ceph_volume_disk_info = CephVolumeInfo()
                fsid = ''
                osd_name = ''
                for element in osd_info:
                    if element['type'] == 'block' or element['type'] == 'data':
                        fsid = element['tags']['ceph.cluster_fsid']
                        if len(fsid) > 0 and fsid != cluster_fsid:
                            continue
                        # if not ['tags']['ceph.cluster_fsid'] or element['tags']['ceph.cluster_fsid'] != cluster_fsid:
                        ceph_volume_disk_info.osd_id = osd_id
                        ceph_volume_disk_info.osd_uuid = element['tags']['ceph.osd_fsid']
                        if len(element['devices']) > 0:
                            for device in element['devices']:
                                part_name = ceph_disk.get_dev_name(device)
                                osd_name = ceph_disk.get_device_name(part_name)
                                ceph_volume_disk_info.devices.append(osd_name)

                        # if there is no devices (physical disks) exists
                        # get them from get_physical_disks function by volume group name

                        else:
                            vg_name = element['vg_name']
                            lv_name = element['lv_name']
                            ceph_volume_disk_info.lv_name = lv_name
                            ceph_volume_disk_info.vg_name = vg_name
                            physical_list = lvm_lib.get_physical_disks(vg_name)
                            main_devices = list(physical_list["main"])
                            writecache_devices = list(physical_list["writecache"])
                            cache_devices = list(physical_list["dmcache"])

                            if len(main_devices) > 0:
                                for main_dev in main_devices:
                                    main_part_name = ceph_disk.get_dev_name(main_dev)
                                    main_dev_name = ceph_disk.get_device_name(main_part_name)
                                    ceph_volume_disk_info.devices.append(main_dev_name)
                            if len(writecache_devices) > 0:
                                for wcache in writecache_devices:
                                    wcache_partition_name = ceph_disk.get_dev_name(wcache)
                                    ceph_volume_disk_info.linked_cache_part_num.append(
                                        ceph_disk.get_partition_num(wcache_partition_name))
                                    ceph_volume_disk_info.linked_cache.append(wcache_partition_name)
                            elif len(cache_devices) > 0:
                                for cache in cache_devices:
                                    cache_partition_name = ceph_disk.get_dev_name(cache)
                                    ceph_volume_disk_info.linked_cache_part_num.append(
                                        ceph_disk.get_partition_num(cache_partition_name))
                                    ceph_volume_disk_info.linked_cache.append(cache_partition_name)

                        journal_path = ""

                        # if 'ceph.journal_device' in element['tags']:
                        #     journal_path = element['tags']['ceph.journal_device']
                        # if 'ceph.db_device' in element['tags']:
                        #     journal_path = element['tags']['ceph.db_device']
                        uuid = ""

                        # for filestore :
                        if 'ceph.journal_uuid' in element['tags']:
                            uuid = element['tags']['ceph.journal_uuid']

                        # for bluestore :
                        if 'ceph.db_uuid' in element['tags']:
                            uuid = element['tags']['ceph.db_uuid']
                        if len(uuid) > 0 and uuid in partitions_uuid:
                            journal_path = partitions_uuid[uuid]
                        if len(journal_path) > 0:
                            try:
                                if ceph_disk.is_partition(journal_path):
                                    journal_name = get_disk_by_partition(journal_path)
                                    journal_partition_name = ceph_disk.get_dev_name(journal_path)
                                    ceph_volume_disk_info.linked_journal_part_num = ceph_disk.get_partition_num(
                                        journal_partition_name)
                                    if len(osd_name) > 0 and osd_name in journal_name:
                                        continue
                                    ceph_volume_disk_info.linked_journal = journal_name
                            except Exception as ex:
                                logger.error(ex)
                                continue
            except Exception as e:
                logger.exception(e)
                continue

            for device in ceph_volume_disk_info.devices:
                ceph_volumes_disks.update({device: ceph_volume_disk_info})

    return ceph_volumes_disks


########################################################################################################################
def get_ceph_disk_list():
    disk_info_list = []

    # read fsid for our cluster from config file
    fsid = None
    try:
        fsid = ceph_disk.get_fsid(configuration().get_cluster_name())
    except Exception as e:
        pass

    journal_linked_osds = {}

    counter = 0

    while True:
        try:
            ceph_disk_list_devs = ceph_disk.list_devices()
            break
        except Exception as e:
            if counter == 120:
                return disk_info_list
            counter += 1
            logger.error(e)
            time.sleep(1)

    for device in ceph_disk_list_devs:

        no_of_partitions = 0
        no_of_availabe_partitions = 0

        path = device['path']
        name = ceph_disk.get_dev_name(path)

        # check for disk block devices
        if not name.startswith('sd') and not name.startswith('xvd') and not name.startswith('nvme'):
            continue

        di = DiskInfo()
        disk_info_list.append(di)
        di.name = name
        di.usage = DiskUsage.no

        # check if disk is not partitioned
        if 'partitions' not in device:
            continue

        old_osd = False
        # first check for OSD partitions
        for partition in device['partitions']:
            if partition['ptype'] == ptype_osd and 'whoami' in partition:
                if fsid and partition['ceph_fsid'] == fsid:
                    di.usage = DiskUsage.osd
                    di.osd_id = partition['whoami']
                    di.osd_uuid = partition['uuid']

                    if 'journal_dev' in partition:
                        journal = partition['journal_dev']
                        journal_disk = get_disk_by_partition(journal)
                        if journal_disk != name:
                            di.linked_journal = journal_disk
                            if journal_disk not in journal_linked_osds:
                                journal_linked_osds[journal_disk] = []
                            journal_linked_osds[journal_disk].append(di.name)

                    if 'block.db_dev' in partition:
                        journal = partition['block.db_dev']
                        journal_disk = get_disk_by_partition(journal)
                        if journal_disk != name:
                            di.linked_journal = journal_disk
                            if journal_disk not in journal_linked_osds:
                                journal_linked_osds[journal_disk] = []
                            journal_linked_osds[journal_disk].append(di.name)

                    # do not check further partitons
                    break
                else:
                    old_osd = True

        if di.usage == DiskUsage.osd:
            # go to next disk
            continue

        # check for  journal disk
        if not old_osd:
            no_of_partitions = len(device['partitions'])
            for partition in device['partitions']:
                if partition['ptype'] == ptype_journal or partition['ptype'] == ptype_blockdb or partition[
                    'ptype'] == journal_avail_ptype:
                    di.usage = DiskUsage.journal

                    if partition['ptype'] == journal_avail_ptype:
                        no_of_availabe_partitions += 1

                    """
                    if 'journal_for' in partition:
                        journal_for = partition['journal_for']
                        journal_for_disk = get_disk_by_partition(journal_for)
                        di.linked_osds.append(journal_for_disk)
                    """
                # check for cache partition
                if partition['ptype'] == cache_used_ptype or partition['ptype'] == cache_avail_ptype:
                    di.usage = DiskUsage.cache

                    if partition['ptype'] == cache_avail_ptype:
                        no_of_availabe_partitions += 1



        if di.usage == DiskUsage.journal or di.usage == DiskUsage.cache:
            if di.usage == DiskUsage.cache and no_of_partitions > 0:
                di.no_of_partitions = no_of_partitions
                di.no_available_partitions = no_of_availabe_partitions
            # go to next disk
            continue

        # check for mounted partitions
        for partition in device['partitions']:
            if 'mount' in partition:
                mount_path = partition['mount']
                if mount_path is not None and 0 < len(mount_path):
                    di.usage = DiskUsage.mounted
                    # check for system disk
                    if mount_path == '/':
                        di.usage = DiskUsage.system
                        break

    for di in disk_info_list:
        if di.usage == DiskUsage.journal and di.name in journal_linked_osds:
            di.linked_osds = journal_linked_osds[di.name]

    return disk_info_list


########################################################################################################################
def get_disk_list():
    ceph_volume_disks = get_ceph_volumes_info()
    ceph_disk_list = get_ceph_disk_list()
    linked_osds_to_journal = {}

    linked_osds_to_cache = {}

    if len(ceph_volume_disks) == 0:
        return ceph_disk_list

    for disk, disk_info in ceph_volume_disks.iteritems():
        if len(disk_info.linked_journal) > 0:
            if disk_info.linked_journal in linked_osds_to_journal.keys():
                linked_osds_to_journal[disk_info.linked_journal].append(disk)
            else:
                linked_osds_to_journal.update({disk_info.linked_journal: [disk]})

        if len(disk_info.linked_cache) > 0:
            for cache in disk_info.linked_cache:
                cache = '/dev/' + cache
                partition_name = ceph_disk.get_dev_name(cache)
                cache_name = ceph_disk.get_device_name(partition_name)

                if cache_name in linked_osds_to_cache.keys():
                    linked_osds_to_cache[cache_name].append(disk)
                else:
                    linked_osds_to_cache.update({cache_name: [disk]})

    for disk in ceph_disk_list:
        if disk.name in ceph_volume_disks.keys():
            disk.osd_uuid = ceph_volume_disks[disk.name].osd_uuid
            disk.osd_id = ceph_volume_disks[disk.name].osd_id
            disk.linked_journal = ceph_volume_disks[disk.name].linked_journal
            disk.linked_journal_part_num = ceph_volume_disks[disk.name].linked_journal_part_num
            disk.linked_cache = ceph_volume_disks[disk.name].linked_cache
            disk.linked_cache_part_num = ceph_volume_disks[disk.name].linked_cache_part_num
            disk.vg_name = ceph_volume_disks[disk.name].vg_name
            disk.lv_name = ceph_volume_disks[disk.name].lv_name
            disk.usage = 0
        if disk.usage == 3 and disk.name in linked_osds_to_journal.keys():
            for osd in linked_osds_to_journal[disk.name]:
                if osd not in disk.linked_osds:
                    disk.linked_osds.append(osd)

        if disk.usage == 4 and disk.name in linked_osds_to_cache.keys():
            for osd in linked_osds_to_cache[disk.name]:
                if osd not in disk.linked_osds:
                    disk.linked_osds.append(osd)

    disk_list = ceph_disk_list

    return disk_list


########################################################################################################################
def force_activate_osds():
    get_disk_list()
    filestore = False
    config = configuration()
    storage_engine = config.get_cluster_info().storage_engine
    if storage_engine == "filestore":
        filestore = True
    for di in get_disk_list():
        if di.usage != DiskUsage.osd:
            continue
        sleep(30)
        if not is_osd_service_running(di.osd_id):
            if not activate_osd(di.name, filestore=filestore):
                logger.error('Error force activate osd  ' + di.name)


########################################################################################################################
def get_disk_by_partition(partition_path):
    partition_name = ceph_disk.get_dev_name(partition_path)
    disk_name = ceph_disk.get_device_name(partition_name)
    return disk_name


########################################################################################################################
def add_journal(disk_name):
    try:
        dev = '/dev/' + disk_name
        clean_disk(disk_name)
        part_size = ceph_disk.get_conf_with_default(configuration().get_cluster_name(), 'osd_journal_size') + 'M'
        part_name = 'ceph-journal'
        part_code = ptype_journal

        cmd = '/sbin/sgdisk --new=1:0:+' + part_size
        cmd += ' --change-name=1:' + part_name
        cmd += ' --typecode=1:' + part_code
        cmd += ' --mbrtogpt -- ' + dev

        ret = subprocess.call(cmd.split())
        if ret == 0:
            return True

    except Exception as e:
        logger.exception(e)

    return False


########################################################################################################################
def get_disk_list_deploy():
    system_disk = ''
    ceph_disk_list = get_disk_list()
    if ceph_disk_list and len(ceph_disk_list) > 0:
        for disk in ceph_disk_list:
            if disk.usage == DiskUsage.system:
                system_disk = disk.name
                break

    disk_list = disk_util.get_disk_list()
    if disk_list and len(disk_list) > 0:
        for disk in disk_list:
            if disk.name == system_disk:
                disk.usage = DiskUsage.system
                break
    return disk_list


########################################################################################################################
def get_full_disk_list(pid=None):
    __output_split_text = "##petasan##"
    disk_list = []
    ceph_disk_list = get_disk_list()
    ph_disk_list = disk_util.get_disk_list()
    osd_dict = None

    try:
        osd_dict = ceph_osd.ceph_osd_tree(configuration().get_node_info().name)
    except Exception as e:
        logger.error(e.message)
    missing_disk_list = []
    # Set osd id and usage

    if ceph_disk_list and len(ceph_disk_list) > 0:
        for disk in ceph_disk_list:
            for ph_disk in ph_disk_list:
                if ph_disk.name == disk.name:
                    ph_disk.usage = disk.usage
                    ph_disk.osd_id = disk.osd_id
                    ph_disk.osd_uuid = disk.osd_uuid
                    ph_disk.linked_journal = disk.linked_journal
                    ph_disk.linked_osds = disk.linked_osds
                    ph_disk.linked_cache = disk.linked_cache
                    ph_disk.linked_cache_part_num = disk.linked_cache_part_num
                    ph_disk.vg_name = disk.vg_name
                    ph_disk.lv_name = disk.lv_name
                    ph_disk.linked_journal_part_num = disk.linked_journal_part_num
                    ph_disk.no_of_partitions = disk.no_of_partitions
                    ph_disk.no_available_partitions = disk.no_available_partitions
                    disk_list.append(ph_disk)
                    break
    else:
        disk_list.extend(ph_disk_list)

    health_test = Smart().get_overall_health()
    for disk in disk_list:
        if disk.name in health_test:
            disk.smart_test = health_test[disk.name]

    # get all running jobs
    job_manager = JobManager()
    job_list = job_manager.get_running_job_list()

    # Set disk osd status
    for node_disk in disk_list:
        # Set osd status [up, down]
        if node_disk.usage == DiskUsage.osd:
            status = None
            if osd_dict and node_disk.osd_id is not None:
                status = osd_dict.get(int(node_disk.osd_id), None)
            if str(ceph_osd.get_osd_id(node_disk.osd_uuid)) == "-1":
                node_disk.status = OsdStatus.no_status
                node_disk.usage = DiskUsage.mounted
                node_disk.osd_id = -1
            elif status is not None:
                node_disk.status = status
            else:
                node_disk.status = OsdStatus.no_status

        disk_name_parameter = "-disk_name {}".format(node_disk.name)
        disk_id_parameter = "-id {}".format(node_disk.osd_id)

        # loop on running job list
        for j in job_list:
            # Set osd status [deleting , adding]
            if j.type == JobType.ADDDISK and str(j.params).find(str(disk_name_parameter)) > -1:
                node_disk.status = OsdStatus.adding
            elif j.type == JobType.ADDJOURNAL and str(j.params).find(str(disk_name_parameter)) > -1:
                node_disk.status = OsdStatus.adding_journal
            elif j.type == JobType.ADDCACHE and str(j.params).find(str(disk_name_parameter)) > -1:
                node_disk.status = OsdStatus.adding_cache
            elif j.type == JobType.DELETEOSD and (
                    str(j.params).find(str(disk_name_parameter)) > -1 or str(j.params).find(str(disk_id_parameter)) > -1):
                node_disk.status = OsdStatus.deleting
            elif j.type == JobType.DELETEJOURNAL and str(j.params).find(str(disk_name_parameter)) > -1:
                node_disk.status = OsdStatus.deleting
            elif j.type == JobType.DELETECACHE and str(j.params).find(str(disk_name_parameter)) > -1:
                node_disk.status = OsdStatus.deleting

            # Check if the job completed and has error to return it
            elif pid and j.id == int(pid):
                job_output = job_manager.get_job_output(j)
                if job_output is None:
                    continue
                job_output = str(job_output).strip()
                if job_output != "":
                    # We expect our custom messages appear after __output_split_text.
                    out_arr = job_output.split(__output_split_text)
                    if out_arr > 1:
                        node_disk.error_message = out_arr[1]
                        job_manager.remove_job(j.id)

    if not osd_dict or len(osd_dict.items()) == 0:
        return disk_list
    # If there is an osd found in ceph tree and this osd not has disk.
    for osd_id, osd_status in osd_dict.items():
        is_missing = True
        for disk in disk_list:
            if str(disk.osd_id) == str(osd_id):
                is_missing = False
                break
        if is_missing:
            disk = DiskInfo()
            disk.osd_id = osd_id
            disk.status = osd_status
            disk.usage = DiskUsage.osd
            missing_disk_list.append(disk)
    disk_list.extend(missing_disk_list)

    return disk_list


########################################################################################################################
def get_disk_info(disk_name):
    disk_infos = get_full_disk_list()
    for di in disk_infos:
        if di.name == disk_name:
            return di

    return None


########################################################################################################################
def is_journal_space_avail(disk_name):
    free_disk_space = disk_avail_space(disk_name)
    config = configuration()
    cluster_name = config.get_cluster_name()
    bluestore_block_db_size = ceph_disk.get_journal_size()
    if free_disk_space > bluestore_block_db_size:
        return True
    return False


########################################################################################################################
def get_valid_journal(journal_list=None, clean=True):
    disks = get_disk_list()
    journal_name = None
    min_linked_osds = None
    no_space_avail = 0
    for disk in disks:
        if disk.usage == DiskUsage.journal:

            if journal_list is not None and disk.name not in journal_list:
                continue

            if not is_journal_space_avail(disk.name):
                no_space_avail += 1
                continue
            no_space_avail = 0
            linked_osds_count = len(disk.linked_osds)
            if min_linked_osds is None or linked_osds_count < min_linked_osds:
                min_linked_osds = linked_osds_count
                journal_name = disk.name
                if min_linked_osds == 0:
                    break
    if journal_name is not None and min_linked_osds == 0 and clean == True:
        clean_disk(journal_name)
    return journal_name


########################################################################################################################
def clean_disk(disk_name):
    logger.info('Start cleaning disk : ' + disk_name)
    zapper = Zapper()
    if not zapper.clean(disk_name):
        return False

    return True


########################################################################################################################
def get_external_journal(journal):
    journal_part_name = ""
    # check for available journals in the disk
    avail_journal_list = get_partitions_by_type(journal, journal_avail_ptype)
    if avail_journal_list is not None and len(avail_journal_list) > 0:
        logger.info('available journal partition found and will be reused.')

        # get journal size from configuration file based on storage engine
        journal_size = ceph_disk.get_journal_size()

        # loop on avail journals and choose the first one which => journal_size
        for journal_part in avail_journal_list:
            journal_part_size = ceph_disk.get_partition_size(journal_part)
            if journal_part_size >= journal_size:
                journal_part_name = journal_part
                break

    if len(journal_part_name) > 0:

        if not zap_partition(journal_part_name):
            return False
        # change uuid of journal partition to new part_uuid
        part_uuid = uuid.uuid4()

        if not set_partition_uuid(journal_part_name, part_uuid):
            return False
        # change ptype of journal partition to ptype_blockdb
        if not set_partition_type(journal_part_name, ptype_blockdb):
            return False
    else:
        logger.info('creating new journal partition.')
        journal_part_num = ceph_disk.create_journal_partition(journal)
        if journal_part_num is None:
            return None
        journal_part_name = ceph_disk.get_partition_name(journal, journal_part_num)
    return journal_part_name


########################################################################################################################
def prepare_osd(device_name, journal=None):
    config = configuration()
    storage_engine = config.get_cluster_info().storage_engine
    if storage_engine == "filestore":
        return prepare_filestore(device_name, journal)
    return prepare_bluestore(device_name, journal)


########################################################################################################################
def prepare_bluestore(device_name, journal=None):
    logger.info('Start prepare bluestore OSD : ' + device_name)
    journal_part_name = ""
    disk_name = ""
    osd_id = ""

    # Check if device is physical or logical :
    lv = lvm_lib.is_lv(device_name)

    if not lv:
        # Create partition with full disk size
        disk_name = device_name
        osd_part_num = ceph_disk.create_osd_partition(device_name)
        osd_part_name = ceph_disk.get_partition_name(device_name, osd_part_num)
        osd_part_name = "/dev/" + osd_part_name

    else:
        osd_part_name = device_name
        # Get the origin disk of volume group to be used in OSD activation :
        vg_name = device_name.split("/")[0]

        # Get the OSD id from VG name :
        osd_id = vg_name.split(".")[1]
        logger.info("OSD_ID = {}".format(osd_id))

        physical_list = lvm_lib.get_physical_disks(vg_name)
        main_devices = list(physical_list["main"])

        if len(main_devices) > 0:
            part_name = main_devices[0]
            partition_name = ceph_disk.get_dev_name(part_name)
            disk_name = ceph_disk.get_device_name(partition_name)

    cmd = 'ceph-volume --log-path ' + CEPH_VOLUME_LOG_PATH + ' lvm prepare '
    cmd += ' --bluestore --data ' + osd_part_name

    if len(osd_id) > 0:
        cmd += ' --osd-id ' + osd_id

    if journal is not None and 0 < len(journal):
        journal_part_name = get_external_journal(journal)
        if journal_part_name is None:
            return False
        cmd += ' --block.db /dev/' + journal_part_name

    logger.info('Starting : ' + cmd)
    if not call_cmd_2(cmd):
        logger.error('Error executing : ' + cmd)
        # After the failure of adding OSD , change ptype of journal partition to "journal_avail_ptype" :
        if journal_part_name != "":
            set_journal_part_avail(journal_part_name)
        return False

    # Activating OSD :
    activate_osd(disk_name)
    return True


########################################################################################################################
def prepare_filestore(device_name, journal=None):
    # clean_disk(disk_name)
    logger.info('Start prepare filestore OSD : ' + device_name)
    journal_part_name = ""
    journal_option = ""
    disk_name = ""
    journal_path = '/dev/' + journal

    if ceph_disk.is_partition(journal_path):
        journal_option = ' --journal /dev/' + journal
    else:
        if journal is not None and 0 < len(journal):
            journal_part_name = get_external_journal(journal)
            if journal_part_name is None:
                return False
            journal_option = ' --journal /dev/' + journal_part_name

    # Check if device is physical or logical :
    lv = lvm_lib.is_lv(device_name)
    if not lv:
        # create partition with full disk size
        disk_name = device_name
        osd_part_num = ceph_disk.create_osd_partition(device_name)
        osd_part_name = ceph_disk.get_partition_name(device_name, osd_part_num)
        osd_part_name = "/dev/" + osd_part_name

    else:
        osd_part_name = device_name
        # Get the origin disk of volume group to be used in OSD activation :
        vg_name = device_name.split("/")[0]
        physical_list = lvm_lib.get_physical_disks(vg_name)
        main_devices = list(physical_list["main"])

        if len(main_devices) > 0:
            part_name = main_devices[0]
            partition_name = ceph_disk.get_dev_name(part_name)
            disk_name = ceph_disk.get_device_name(partition_name)

    cmd = 'ceph-volume --log-path ' + CEPH_VOLUME_LOG_PATH + ' lvm prepare '
    cmd += ' --filestore --data ' + osd_part_name + journal_option
    logger.info('Starting : ' + cmd)

    if not call_cmd_2(cmd):
        logger.error('Error executing : ' + cmd)
        # after add osd fail change ptype of journal partition to journal_avail_ptype
        if journal_part_name != "":
            set_journal_part_avail(journal_part_name)
        return False

    # Activating OSD :
    activate_osd(disk_name, True)
    return True



########################################################################################################################
def is_osd_service_running(osd_id):
    status = False
    cmd = '/bin/systemctl status ceph-osd@%s' % osd_id
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    if '(running)' in str(out):
        status = True
    else:
        status = False
    return status


########################################################################################################################
def wait_for_osd_up(disk_name):
    count = 5
    while 0 < count:
        di = get_disk_info(disk_name)
        if di is None:
            break
        if di.usage == DiskUsage.osd and is_osd_service_running(di.osd_id):
            break
        sleep(10)
        count -= 1


########################################################################################################################
def disk_avail_space(disk_name):
    """
    DOCSTRING : this function is to return free space of any given disk including space of unused partitions
    Args : disk name
    Returns : free disk space
    """
    # frist get num of unused journal partitions

    unused_partitions_ls = get_partitions_by_type(disk_name, journal_avail_ptype)
    total_unused_partitions_size = 0
    for part in unused_partitions_ls:
        total_unused_partitions_size += ceph_disk.get_partition_size(part)

    output, err = exec_command(
        "parted /dev/{} unit B print free | grep 'Free Space' | tail -n1 | awk '{{print $3}}'".format(disk_name))
    free_disk_space = re.findall(r'-?\d+\.?\d*', output)
    free_disk_space = float(free_disk_space[0]) + total_unused_partitions_size
    return free_disk_space


########################################################################################################################
def set_partition_type(part_name, part_type):
    logger.info('Start setting partition type for ' + part_name)
    disk_name = ceph_disk.get_device_name(part_name)
    part_num = ceph_disk.get_partition_num(part_name)
    cmd = 'sgdisk -t ' + part_num + ':' + part_type + ' /dev/' + disk_name
    logger.info('Starting ' + cmd)
    if not call_cmd_2(cmd):
        logger.error('Error executing ' + cmd)
        return False
    ceph_disk.probe_part(disk_name)

    return True


########################################################################################################################
def set_journal_part_avail(partition_name):
    return set_partition_type(partition_name, journal_avail_ptype)


########################################################################################################################
def get_partitions_by_type(disk_name, part_type):
    try:
        partition_list = []
        dev = "/dev/" + disk_name
        partitions = ceph_disk.list_partitions_device(dev)
        for partition in partitions:
            partition_type = ceph_disk.get_partition_type(partition)
            if partition_type == part_type:
                partition_list.append(partition)
        return partition_list

    except Exception as e:
        logger.error("error getting partitions type list. ", e.message)
        return None


########################################################################################################################
def activate_osd(disk_name, filestore=False):
    logger.info('starting activate osd. ')
    ceph_volume_dict = get_ceph_volumes_info()
    engine = "--bluestore"
    if filestore:
        engine = "--filestore"

    if len(ceph_volume_dict) > 0:
        osd_id = ceph_volume_dict[disk_name].osd_id
        osd_uuid = ceph_volume_dict[disk_name].osd_uuid
        cmd = 'ceph-volume --log-path ' + CEPH_VOLUME_LOG_PATH + ' lvm activate {} {} {}'.format(engine, osd_id,
                                                                                                 osd_uuid)
        logger.info('Starting : ' + cmd)
        if not call_cmd_2(cmd):
            logger.error('Error executing : ' + cmd)
            logger.error('Error activating osd.')

            logger.info('Try activate all osds fallback ...')
            if filestore:
                if not call_cmd_2('ceph-volume lvm activate --filestore --all'):
                    logger.error('Error activate osd fallback.')
                    return False
            else:
                if not call_cmd_2('ceph-volume lvm activate --all'):
                    logger.error('Error activate osd fallback.')
                    return False

    return True


########################################################################################################################
def set_partition_uuid(part_name, part_uuid):
    logger.info('Start setting partition uuid for ' + part_name)
    disk_name = ceph_disk.get_device_name(part_name)
    part_num = ceph_disk.get_partition_num(part_name)
    cmd = 'sgdisk -u ' + part_num + ':' + str(part_uuid) + ' /dev/' + disk_name
    logger.info('Starting ' + cmd)
    if not call_cmd_2(cmd):
        logger.error('Error executing ' + cmd)
        return False
    ceph_disk.probe_part(disk_name)
    return True


########################################################################################################################
def zap_partition(part_name):
    logger.info('Start zapping partition ' + part_name)
    cmd = 'ceph-volume --log-path ' + CEPH_VOLUME_LOG_PATH + ' lvm zap /dev/' + part_name
    logger.info('Starting ' + cmd)
    if not call_cmd_2(cmd):
        logger.error('Error executing ' + cmd)
        logger.error('Error zapping ' + part_name)
        return False
    return True


########################################################################################################################
def add_cache(disk_name, partitions=None):
    try:
        part_name = 'cache'
        part_code = cache_avail_ptype
        # part_size = 64 * 1024       # in MegaBytes
        cache_size = ceph_disk.get_dev_size('/dev/' + disk_name)  # comes in megabytes
        cache_size_gb = cache_size / 1024

        # If adding Cache from Deployment phase --> No number of partitions sent :
        if partitions is None:
            if cache_size_gb < 192:
                partitions = 2
            elif cache_size_gb >= 192 or cache_size_gb < 256:
                partitions = 3
            elif cache_size_gb >= 256:
                partitions = 4

        partitions = int(partitions)

        # Type casting for "partitions" from str to int , it comes str from the script
        part_size = cache_size / partitions

        for i in range(partitions):
            part_uuid = uuid.uuid4()

            # If it is the last partition , take whatever size left in the disk
            if i == (partitions - 1):
                part_size = 0

            if not ceph_disk.create_partition(disk_name, part_name, part_size, part_uuid, part_code):
                return False

        return True

    except Exception as e:
        logger.exception(e)


########################################################################################################################
def is_cache_partition_avail(disk_name):
    avail_partition_list = get_partitions_by_type(disk_name, cache_avail_ptype)

    if avail_partition_list is not None and len(avail_partition_list) > 0:
        return True

    return False


########################################################################################################################
def has_valid_cache(node_name):
    cmd = "python {} {}".format(ConfigAPI().get_admin_manage_node_script(), "valid-cache")
    stdout, stderr = exec_command(cmd)

    if 'None' in stdout:
        return False
    else:
        return True


########################################################################################################################
def get_valid_cache(cache_list=None):
    cache_name = None
    max_avail_partitions = 0

    # Get all disks :
    # ---------------
    disks = get_disk_list()

    for disk in disks:
        if disk.usage == DiskUsage.cache:
            if cache_list is not None and disk.name not in cache_list:
                continue

        if not is_cache_partition_avail(disk.name):
            continue

        avail_partition_list = get_partitions_by_type(disk.name, cache_avail_ptype)

        if avail_partition_list is not None and len(avail_partition_list) > max_avail_partitions:
            max_avail_partitions = len(avail_partition_list)
            cache_name = disk.name

    return cache_name


########################################################################################################################
def set_cache_part_avail(partition_name):
    return set_partition_type(partition_name, cache_avail_ptype)


########################################################################################################################
def delete_unused_ceph_volume_services():
    # get all uuids of current osds using ceph-volume list
    ceph_volume_list = get_ceph_volumes_info()
    if not ceph_volume_list:
        return False

    current_osd_uuids = [ceph_volume_list[cv].osd_uuid for cv in ceph_volume_list]

    # get all stored osd services in os to disable old ones
    systemd_path = "/etc/systemd/system/multi-user.target.wants/"
    osd_services_list = os.listdir(systemd_path)
    for osd_service in osd_services_list:
        if osd_service.startswith("ceph-volume@lvm"):
            service_uuid = osd_service[18:].split(".")[0]
            if service_uuid not in current_osd_uuids:
                cmd = 'systemctl disable {}'.format(osd_service)
                logger.info('Starting ' + cmd)
                if not call_cmd_2(cmd):
                    logger.error('Error executing ' + cmd)
                    logger.error('Error disabling old osd service ')
                    return False
                logger.info('success executing ' + cmd)

    return True


########################################################################################################################
def get_next_osd_id():
    cmd = "ceph osd create"
    ret, stdout, stderr = exec_command_ex(cmd)
    if ret != 0:
        if stderr:
            logger.error("Error in getting the next OSD id , error : {}".format(stderr))
            return ""

    osd_id = stdout.rstrip().strip()

    # Remove OSD from ceph crush map :
    ceph_osd.delete_osd_from_crush_map(int(osd_id))

    return str(osd_id)
