#!/usr/bin/python
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

import argparse
import sys

from PetaSAN.core.cache.cache import Cache
from PetaSAN.core.cache.cache_manager import CacheManager
from PetaSAN.core.ceph.ceph_osd import *
from PetaSAN.core.ceph import ceph_osd, ceph_disk
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.enums import DiskUsage
from PetaSAN.core.common.messages import gettext
from PetaSAN.core.common.smart import Smart
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.consul.base import BaseAPI
from PetaSAN.core.ceph import ceph_disk_lib
from PetaSAN.core.lvm.lvm_lib import *
from PetaSAN.core.ssh.ssh import ssh


class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        subparser = parser.add_subparsers()

        subp_node_list = subparser.add_parser('disk-list')
        subp_node_list.set_defaults(func=node_disk_list_json)
        subp_node_list.add_argument('-pid', help='Process id or running job.', required=True)

        subp_delete_osd = subparser.add_parser('delete-osd')
        subp_delete_osd.set_defaults(func=delete_osd)
        subp_delete_osd.add_argument('-id', help='OSD id.', required=True)
        subp_delete_osd.add_argument('-disk_name', help='disk name.', required=True)

        subp_add_osd = subparser.add_parser('add-osd')
        subp_add_osd.set_defaults(func=add_osd)
        subp_add_osd.add_argument('-disk_name', help='Disk name that will add to ceph osds.', required=True)
        subp_add_osd.add_argument('-journal', help='Journal disk name.', default="")
        subp_add_osd.add_argument('-cache', help='Cache disk name.', default="")
        subp_add_osd.add_argument('-cache_type', help='The cache type.', default="")

        subp_update_role = subparser.add_parser('update-role')
        subp_update_role.set_defaults(func=update_role)
        subp_update_role.add_argument(
            '-is_storage',
            help='Update role of storage service.Set argument to -1 to avoid this argument from update this role',
            required=True)
        subp_update_role.add_argument(
            '-is_iscsi',
            help='Update role of iscsi service.Set argument to -1 to avoid this argument from update this role. ',
            required=True)
        subp_update_role.add_argument(
            '-is_backup',
            help='Update role of backup service.Set argument to -1 to avoid this argument from update this role. ',
            required=True)

        subp_node_log = subparser.add_parser('node-log')
        subp_node_log.set_defaults(func=get_log)

        subp_disk_health = subparser.add_parser('disk-health')
        subp_disk_health.set_defaults(func=node_disk_health)

        subp_add_journal = subparser.add_parser('add-journal')
        subp_add_journal.set_defaults(func=add_journal)
        subp_add_journal.add_argument('-disk_name', help='Disk name that will add to ceph journal.', required=True)

        subp_disk_avail_space = subparser.add_parser('disk-avail-space')
        subp_disk_avail_space.set_defaults(func=disk_avail_space)
        subp_disk_avail_space.add_argument('-disk_name', help='Disk name that will get its free space.', required=True)

        subp_valid_journal = subparser.add_parser('valid-journal')
        subp_valid_journal.set_defaults(func=get_valid_journal)

        subp_delete_journal = subparser.add_parser('delete-journal')
        subp_delete_journal.set_defaults(func=delete_journal)
        subp_delete_journal.add_argument('-disk_name', help='Disk name that will format.', required=True)

        subp_add_cache = subparser.add_parser('add-cache')
        subp_add_cache.set_defaults(func=add_cache)
        subp_add_cache.add_argument('-disk_name', help='Disk name that will add to caching disk.', required=True)
        subp_add_cache.add_argument('-partitions', help='Number of partitions.', required=True)

        subp_delete_cache = subparser.add_parser('delete-cache')
        subp_delete_cache.set_defaults(func=delete_cache)
        subp_delete_cache.add_argument('-disk_name', help='Disk name that will format.', required=True)

        subp_valid_cache = subparser.add_parser('valid-cache')
        subp_valid_cache.set_defaults(func=get_valid_cache)

        subp_cache_partition_avail = subparser.add_parser('cache-partition-avail')
        subp_cache_partition_avail.set_defaults(func=is_cache_partition_avail)
        subp_cache_partition_avail.add_argument('-disk_name', help='Disk name that will be checked if it has '
                                                                   'available cache partitions or not.', required=True)

        args = parser.parse_args()

        return args


__output_split_text = "## petasan ##"


def main_catch(func, args):
    try:
        func(args)

    except Exception as e:
        logger.exception(e.message)
        logger.error("Error while run command.")


def main(argv):
    args = Prepare().parser()
    main_catch(args.func, args)


# ======================================================================================================================
def node_disk_list_json(args):
    print (json.dumps([o.get_dict() for o in ceph_disk_lib.get_full_disk_list(args.pid)]))


# ======================================================================================================================
def node_disk_health(args):
    health_test = Smart().get_overall_health()

    print(json.dumps(health_test))


# ======================================================================================================================
def delete_osd(args):
    try:
        disk_list = ceph_disk_lib.get_disk_list()
        journal_partition = "no_journal"
        linked_cache_list = []
        vg_name = ""

        for disk in disk_list:
            if disk.name == args.disk_name:
                if len(disk.linked_journal) > 0:
                    journal_partition = disk.linked_journal + disk.linked_journal_part_num

                if len(disk.linked_cache) > 0:
                    linked_cache_list = disk.linked_cache
                    vg_name = disk.vg_name

                if len(linked_cache_list) > 0 and journal_partition != "no_journal":
                    break

        # Remove OSD from Ceph Crush Map :
        # --------------------------------
        ceph_osd.delete_osd_from_crush_map(int(args.id))
        ceph_osd.delete_osd(int(args.id), args.disk_name)

        # If Cache was used :
        # -------------------
        if vg_name and len(linked_cache_list) > 0:
            cm = CacheManager()
            cache_type = cm.get_cache_type(args.disk_name)
            cm.delete(args.disk_name, cache_type)
            for cache_part in linked_cache_list:
                ceph_disk_lib.clean_disk(cache_part)
                stat = ceph_disk_lib.set_cache_part_avail(cache_part)
                if not stat:
                    logger.error("Can't set cache partition {} available for osd {}".format(cache_part,
                                                                                            args.disk_name))

        #  Get the Volume Group name (VG) of the selected OSD --> in order to deactivate it first before clean_disk() :
        # -------------------------------------------------------------------------------------------------------------
        osd_vg = get_vg_from_disk(args.disk_name)
        if osd_vg is not None:
            deactivate_vg(osd_vg)

        #  Clean Disk :
        # -------------
        ceph_disk_lib.clean_disk(args.disk_name)

        # Remove unused OSD Systemd Service after deleting the OSD :
        # ----------------------------------------------------------
        ceph_disk_lib.delete_unused_ceph_volume_services()

        if journal_partition is not "no_journal":
            journal_path = '/dev/' + journal_partition
            if ceph_disk.is_partition(journal_path):
                stat = ceph_disk_lib.set_journal_part_avail(journal_partition)
                if not stat:
                    logger.error("Can't set journal partition {} available for osd {}".format(journal_partition,
                                                                                              args.disk_name))

    except Exception as ex:
        logger.error(ex.message)


# ======================================================================================================================
def add_osd(args):
    # Read arguments #
    disk_name = str(args.disk_name)
    journal = str(args.journal)
    cache = str(args.cache)
    cache_type = str(args.cache_type)
    device_name = disk_name

    try:
        di = ceph_disk_lib.get_disk_info(disk_name)

        #  Check if disk is not used already as OSD #
        if di.usage == DiskUsage.osd:
            print(__output_split_text)
            print(gettext('core_scripts_admin_add_osd_disk_is_osd_err'))
            return

        #  Cleaning disk  #
        if not ceph_disk_lib.clean_disk(disk_name):
            print(__output_split_text)
            print(gettext('core_scripts_admin_add_osd_cleaning_err'))
            return

        # Journals #

        if journal == "" or journal is None:
            # If user didn't select a journal for disk and cluster is filestore
            logger.info(
                "User didn't select a journal for disk {}, so the journal will be on the same disk.".format(disk_name))
            config = configuration()
            storage_engine = config.get_cluster_info().storage_engine
            if storage_engine == "filestore":
                # manually create journal partition in the same disk for filestore
                journal_part_num = ceph_disk.create_journal_partition(device_name, external=False)
                journal = ceph_disk.get_partition_name(device_name, journal_part_num)

        # If journal value equals "auto" :
        elif journal == "auto":
            logger.info("Auto select journal for disk {}.".format(disk_name))
            journal = ceph_disk_lib.get_valid_journal()

            if journal is None:
                print (__output_split_text)
                print (gettext('core_scripts_admin_add_osd_journal_err'))
                logger.error(gettext('core_scripts_admin_add_osd_journal_err'))
                return
            logger.info(
                "User selected Auto journal, selected device is {} disk for disk {}.".format(journal, disk_name))

        # If user selected a specific journal for disk :
        else:
            ji = ceph_disk_lib.get_disk_info(journal)
            if ji is None or ji.usage != DiskUsage.journal:
                print (__output_split_text)
                print (gettext('core_scripts_admin_osd_adding_err'))
                logger.info("User selected journal {} does not exist or is not a valid journal.".format(journal))
                return

            if len(ji.linked_osds) == 0:
                ceph_disk_lib.clean_disk(journal)

            logger.info("User selected journal {} disk for disk {}.".format(journal, disk_name))

        ############
        #  Caches  #
        ############
        # If user didn't select a cache for disk :
        if cache == "":
            logger.info("User didn't select a cache for disk {}.".format(disk_name))

        # If cache value equals "auto" :
        elif cache == "auto":
            logger.info("Auto select cache for disk {}.".format(disk_name))
            cache = ceph_disk_lib.get_valid_cache()

            if cache is None:
                print(__output_split_text)
                print(gettext('core_scripts_admin_add_osd_cache_err'))
                logger.error(gettext('core_scripts_admin_add_osd_cache_err'))
                return

            logger.info("User selected Auto cache, selected device is {} disk for disk {}.".format(cache, disk_name))

        # If user selected a specific cache for disk :
        else:
            selected_cache = ceph_disk_lib.get_disk_info(cache)

            if selected_cache is None or selected_cache.usage != DiskUsage.cache:
                print (__output_split_text)
                print (gettext('core_scripts_admin_osd_adding_err'))
                logger.info("User selected cache {} does not exist or is not a valid cache.".format(cache))
                return

        logger.info("User selected cache {} disk for disk {}.".format(cache, disk_name))

        # Creating "write-lvm" before creating "OSD" #
        # where lv_name of HDD = main , lv_name of SSD = cache , and vg_name = ps-wc-osd_000{rand_num}
        # --------------------------------------------------------------------------------------------
        main_path = None
        cache_part = None
        vg_name = None

        if cache is not None and len(cache) > 0:
            # create cache #
            cm = CacheManager()
            main_path, cache_part = cm.create(disk_name, cache, cache_type)  # main_path = lv_path
            # = vg_name + "/" + main_lv_name
            if main_path is not None and cache_part is not None:
                vg_name = main_path.split("/")[0]  # For renaming VG after the osd id later
                device_name = main_path

        #################
        # Preparing OSD #
        #################
        if not ceph_disk_lib.prepare_osd(device_name, journal):
            if cache_part is not None:
                cm = CacheManager()
                cm.delete(disk_name, cache_type)
                # After the failure of adding OSD , clean both disk & cache partition and
                # change ptype of cache partition to "cache_avail_ptype" :
                ceph_disk_lib.clean_disk(disk_name)
                ceph_disk_lib.clean_disk(cache_part)
                ceph_disk_lib.set_cache_part_avail(cache_part)

            print(__output_split_text)
            print(gettext('core_scripts_admin_osd_adding_err'))
            return

        ceph_disk_lib.wait_for_osd_up(disk_name)

    except Exception as ex:
        err = "Cannot add osd for disk {} , Exception is : {}".format(disk_name, ex.message)
        logger.exception(err)
        print(err)
        print(__output_split_text)
        print(gettext('core_scripts_admin_add_osd_exception'))


# ======================================================================================================================
def get_log(args):
    with open(ConfigAPI().get_log_file_path(), 'r') as f:
        print f.read()


# ======================================================================================================================
def update_role(args):
    logger.info("Update roles.")
    config_api = ConfigAPI()
    try:
        cluster_config = configuration()
        node_info = cluster_config.get_node_info()
        is_dirty = False

        if str(args.is_storage) == '-1' and str(args.is_iscsi) == '-1':
            return
        if str(args.is_storage) == "1":
            if not node_info.is_storage:
                logger.info("Update roles 1.")
                node_info.is_storage = True
                cluster_config.update_node_info(node_info)
                is_dirty = True
                logger.info("Update node storage role to true")

        else:
            # ToDO
            pass

        if str(args.is_backup) == "1":
            if not node_info.is_backup:
                node_info.is_backup = True
                cluster_config.update_node_info(node_info)
                is_dirty = True
                logger.info("Update node backup role to true")
        else:
            # ToDO
            pass

        if str(args.is_iscsi) == "1":
            if not node_info.is_iscsi:
                node_info.is_iscsi = True
                cluster_config.update_node_info(node_info)
                is_dirty = True
                logger.info("Update node iscsi role to true")

                path = config_api.get_service_files_path()
                logger.info("Starting PetaSAN service")
                cmd = "python {}{} >/dev/null 2>&1 &".format(path, config_api.get_petasan_service())
                exec_command(cmd)
        else:
            # ToDO
            pass

        if is_dirty:

            if node_info.is_management:
                try:
                    ssh_obj = ssh()
                    cluster_info = cluster_config.get_cluster_info()
                    for node in cluster_info.management_nodes:
                        if node['name'] == node_info.name:
                            node['is_iscsi'] = node_info.is_iscsi
                            node['is_backup'] = node_info.is_backup
                            break
                    cluster_config.set_cluster_network_info(cluster_info)
                    cluster_info_file_path = config_api.get_cluster_info_file_path()
                    consul_api = ConsulAPI()
                    node_list = consul_api.get_node_list()
                    for node in node_list:
                        ssh_obj.copy_file_to_host(node.name, cluster_info_file_path)
                except Exception as e:
                    logger.error(e)
                    print(-1)

            consul_base_api = BaseAPI()

            consul_base_api.write_value(config_api.get_consul_nodes_path() + cluster_config.get_node_name(),
                                        cluster_config.get_node_info().write_json())
            print 1

    except Exception as ex:
        logger.exception(ex.message)
        print -1

    return


# ======================================================================================================================
def add_journal(args):
    try:
        di = ceph_disk_lib.get_disk_info(args.disk_name)

        if di is None:
            print (__output_split_text)
            print (gettext('core_scripts_admin_journal_adding_err'))
            logger.error("The disk does not exits.")
            return

        if di.usage == DiskUsage.osd or di.usage == DiskUsage.journal or di.usage == DiskUsage.system:
            print (__output_split_text)
            print (gettext('core_scripts_admin_add_journal_disk_on_use_err'))
            return

        if not ceph_disk_lib.clean_disk(args.disk_name):
            print (__output_split_text)
            print (gettext('core_scripts_admin_journal_adding_err'))
            return

        if not ceph_disk_lib.add_journal(args.disk_name):
            print (__output_split_text)
            print (gettext('core_scripts_admin_journal_adding_err'))
            return

        return

    except Exception as ex:
        err = "Cannot add journal for disk {} , Exception is {}".format(args.disk_name, ex.message)
        logger.error(err)
        print (err)
        print (__output_split_text)
        print (gettext('core_scripts_admin_add_journal_exception'))


# ======================================================================================================================
def delete_journal(args):
    try:
        di = ceph_disk_lib.get_disk_info(args.disk_name)

        if di is None or di.usage != DiskUsage.journal:
            print (__output_split_text)
            print (gettext('core_scripts_admin_delete_journal_err'))
            return

        if not ceph_disk_lib.clean_disk(args.disk_name):
            print (__output_split_text)
            print (gettext('core_scripts_admin_delete_journal_err'))
            return

        return

    except Exception as ex:
        logger.exception(ex)
        print (__output_split_text)
        print (gettext('core_scripts_admin_delete_journal_err'))
        return


# ======================================================================================================================
# --------- New Code ---------- #
def disk_avail_space(args):
    disk_free_space = ceph_disk_lib.disk_avail_space(args.disk_name)
    print(json.dumps(disk_free_space))


def get_valid_journal(args):
    valid_journal = ceph_disk_lib.get_valid_journal(clean=False)
    if valid_journal is None:
        print(json.dumps("None"))
    print(json.dumps(valid_journal))


# ======================================================================================================================
def add_cache(args):
    try:
        di = ceph_disk_lib.get_disk_info(args.disk_name)

        if di is None:
            print ("\n")
            print (__output_split_text)
            print (gettext('core_scripts_admin_cache_adding_err'))
            logger.error("The disk does not exits.")
            return

        if di.usage == DiskUsage.osd or di.usage == DiskUsage.journal or di.usage == DiskUsage.cache or di.usage == DiskUsage.system:
            print ("\n")
            print (__output_split_text)
            print (gettext('core_scripts_admin_add_cache_disk_on_use_err'))
            return

        if not ceph_disk_lib.clean_disk(args.disk_name):
            print ("\n")
            print (__output_split_text)
            print (gettext('core_scripts_admin_add_cache_cleaning_err'))
            return

        if not ceph_disk_lib.add_cache(args.disk_name, args.partitions):
            print ("\n")
            print (__output_split_text)
            print (gettext('core_scripts_admin_add_cache_exception'))
            return

        return

    except Exception as ex:
        err = "Cannot add lvm for disk {} , Exception is {}".format(args.disk_name, ex.message)
        logger.error(err)
        print (err)
        print (__output_split_text)
        print (gettext('core_scripts_admin_add_cache_exception'))


# ======================================================================================================================
def get_valid_cache(args):
    valid_cache = ceph_disk_lib.get_valid_cache()

    if valid_cache is None:
        print(json.dumps("None"))
    else:
        print (json.dumps(valid_cache))


# ======================================================================================================================
def is_cache_partition_avail(args):
    is_avail = ceph_disk_lib.is_cache_partition_avail(args.disk_name)

    if not is_avail:
        print(json.dumps("False"))
    else:
        print(json.dumps("True"))


# ======================================================================================================================
def delete_cache(args):
    try:
        di = ceph_disk_lib.get_disk_info(args.disk_name)

        if di is None or di.usage != DiskUsage.cache:
            print (__output_split_text)
            print (gettext('core_scripts_admin_delete_cache_err'))
            return

        if not ceph_disk_lib.clean_disk(args.disk_name):
            print (__output_split_text)
            print (gettext('core_scripts_admin_delete_cache_err'))
            return

        return

    except Exception as ex:
        logger.exception(ex)
        print (__output_split_text)
        print (gettext('core_scripts_admin_delete_cache_err'))
        return


if __name__ == '__main__':
    main(sys.argv[1:])

