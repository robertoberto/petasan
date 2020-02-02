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

from PetaSAN.core.ceph import ceph_disk as ceph_disk

from PetaSAN.backend.manage_config import ManageConfig
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.ceph.util import get_next_id
from PetaSAN.core.cluster.job_manager import JobManager
from PetaSAN.core.common.CustomException import DiskListException
from PetaSAN.core.common.enums import ManageDiskStatus, DisplayDiskStatus, Status, StopDiskStatus, PathType, \
    NewIPValidation
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.entity.disk_info import DiskMeta, Path
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.entity.job import JobType


class ManageDisk:
    def __init__(self):
        pass

    # ***************************************************
    #                 Add
    # ***************************************************

    def add_disk(self, disk_meta, manual_ips, path_type, paths_count, auth_auto, auto_ip, pool):

        """
        :type path_type: PathType
        :type manual_ips: [string]
        :type paths_count: int
        :type disk_meta: DiskMeta
        """
        cfg = ManageConfig()
        paths = []
        try:
            if not disk_meta.disk_name or not disk_meta.size or type(disk_meta.size) != int:
                return ManageDiskStatus.data_missing
            elif not auth_auto and (not disk_meta.user or not disk_meta.password):
                return ManageDiskStatus.data_missing
            elif not auto_ip and int(paths_count) > 2:
                return ManageDiskStatus.wrong_data
            elif not auto_ip and int(paths_count) != len(manual_ips):
                return ManageDiskStatus.wrong_data
            elif not auto_ip:
                ip_status = cfg.validate_new_iscsi_ips(manual_ips, path_type)
                if ip_status == NewIPValidation.valid:
                    for ip in manual_ips:
                        paths.append(cfg.get_path(ip))
                elif ip_status == NewIPValidation.used_already:
                    return ManageDiskStatus.used_already
                elif ip_status == NewIPValidation.wrong_subnet:
                    return ManageDiskStatus.wrong_subnet
                else:
                    return ManageDiskStatus.wrong_data
            elif auto_ip:
                paths.extend(cfg.get_new_iscsi_ips(path_type, paths_count))
            if not paths or len(paths) == 0:
                return ManageDiskStatus.ip_out_of_range

            new_id = self.__get_next_disk_id()
            disk_meta.id = new_id
            disk_meta.paths = paths
            disk_meta.wwn = self.__get_wwn(new_id)

            if auth_auto:
                disk_meta.user = ""
                disk_meta.password = ""

            disk_meta.iqn = ":".join([cfg.get_iqn_base(), new_id])
            consul_api = ConsulAPI()
            disk_data = consul_api.find_disk(disk_meta.id)

            if disk_data is not None:
                return ManageDiskStatus.disk_exists

            ceph_api = CephAPI()
            status = ceph_api.add_disk(disk_meta, True, pool)
            if status == ManageDiskStatus.done:
                consul_api.add_disk_resource(disk_meta.id, "disk")
                consul_api.add_disk_pool(disk_meta.id, pool)
                i = 0
                for p in paths:
                    i += 1
                    consul_api.add_disk_resource("/".join(["", disk_meta.id, str(i)]), None)

        except DiskListException as e:
            status = ManageDiskStatus.disk_get__list_error
            logger.exception(e.message)
        except Exception as e:
            status = ManageDiskStatus.error
            logger.exception(e.message)
        return status

    # ***************************************************
    #                 Disk List
    # ***************************************************

    # Returns disk metadata on all pools, adds disk status from consul
    def get_disks_meta(self):
        ceph_api = CephAPI()
        consul_api = ConsulAPI()
        ls = ceph_api.get_disks_meta()
        for disk in ls:
            if disk and hasattr(disk, "paths") and not disk.paths:
                disk.status = DisplayDiskStatus.unattached
            elif disk and hasattr(disk, "paths") and disk.paths:
                data = consul_api.find_disk(disk.id)
                if data is not None:
                    disk.status = DisplayDiskStatus.starting
                    if str(data.Flags) == "1":
                        disk.status = DisplayDiskStatus.stopping
                    elif consul_api.is_path_locked(disk.id):
                        disk.status = DisplayDiskStatus.started

                else:
                    disk.status = DisplayDiskStatus.stopped


                job_manager = JobManager()
                job_list = job_manager.get_running_job_list()

                for j in job_list:

                    # Check if the status running
                    if j.is_running:
                        # Set disk status [deleting]
                        if j.type == JobType.DELETE_DISK and str(j.params).find(str(disk.id)) > -1:
                            disk.status = DisplayDiskStatus.deleting

        return ls

    def get_disk(self, disk_id, pool):
        ceph_api = CephAPI()
        return ceph_api.get_disk_meta(disk_id, pool)

    def get_disk_paths(self, disk_id, pool):
        paths_list = CephAPI().get_disk_meta(disk_id, pool).paths
        paths_list_with_node = []
        sessions_dict = ConsulAPI().get_sessions_dict(ConfigAPI().get_iscsi_service_session_name())

        # in case consul lock on disk
        for kv in ConsulAPI().get_disk_paths(disk_id):
            path = Path()
            path_str = paths_list[int(str(kv.Key).split(disk_id + "/")[1]) - 1]
            path.load_json(json.dumps(path_str))
            if hasattr(kv, "Session") and sessions_dict.has_key(kv.Session):

                path.locked_by = sessions_dict.get(kv.Session).Node
                paths_list_with_node.append(path)
            else:
                paths_list_with_node.append(path)

        # in case disk is stopped
        if not paths_list_with_node:

            for path_str in paths_list:
                path = Path()
                path.load_json(json.dumps(path_str))
                paths_list_with_node.append(path)
        return paths_list_with_node

    # ***************************************************
    #                 Start
    # ***************************************************

    def start(self, disk_id, pool):
        try:
            ceph_api = CephAPI()
            consul_api = ConsulAPI()

            attr = ceph_api.read_image_metadata(ConfigAPI().get_image_name_prefix() + disk_id, pool)
            petasan_meta = attr.get(ConfigAPI().get_image_meta_key())
            disk_meta = DiskMeta()
            if petasan_meta:
                disk_meta.load_json(petasan_meta)
            else:
                return Status.error

            consul_api.add_disk_resource(disk_meta.id, "disk")
            consul_api.add_disk_pool(disk_meta.id, pool)
            i = 0
            for p in disk_meta.paths:
                i += 1
                consul_api.add_disk_resource("/".join(["", disk_meta.id, str(i)]), None)

        except Exception as e:
            logger.error("Can not start disk %s" % disk_id)
            logger.exception(e.message)
            return Status.error
        return Status.done

    # ***************************************************
    #                 Stop
    # ***************************************************

    def stop(self, disk_id):
        try:
            consul_api = ConsulAPI()
            kv = consul_api.find_disk(disk_id)
            return consul_api.add_disk_resource(disk_id, "disk", 1, kv.CreateIndex)
        except Exception as ex:
            logger.error("stop disk exception :{}".format(ex.message))
            return ManageDiskStatus.error

    # ***************************************************
    #                 Delete
    # ***************************************************

    def delete_disk(self, disk_id, pool):
        ceph_api = CephAPI()
        consul_api = ConsulAPI()

        ls = ceph_api.get_disks_meta_for_pool(pool)
        try:
            for disk in ls:
                if disk_id == disk.id:

                    if disk and hasattr(disk, "paths") and not disk.paths:
                        disk_status = DisplayDiskStatus.unattached
                    elif disk and hasattr(disk, "paths") and disk.paths:
                        data = consul_api.find_disk(disk.id)
                        if data is not None:
                            disk_status = DisplayDiskStatus.started
                            if str(data.Flags) == "1":
                                disk_status = DisplayDiskStatus.stopping
                        else:
                            disk_status = DisplayDiskStatus.stopped
                    break

                disk_status = None
        except:
            return StopDiskStatus.error

        if disk_status == DisplayDiskStatus.started or disk_status == DisplayDiskStatus.stopping:
            return StopDiskStatus.working

        elif disk_status is None:
            return StopDiskStatus.error

        elif disk_status == DisplayDiskStatus.stopped or disk_status == DisplayDiskStatus.unattached:
            # return ceph_api.delete_disk(disk_id,pool)

            # start: delete disk as a job
            __image_name_prefix = ConfigAPI().get_image_name_prefix()

            # set image_name by disk_id :
            image_name = disk_id

            # if PetaSAN disk :
            if disk_id.isdigit() and (len(disk_id) == 5):
                image_name = __image_name_prefix + str(disk_id)

            jm = JobManager()

            try:
                id = jm.add_job(JobType.DELETE_DISK, image_name + ' ' + pool)
                print("Start Delete image: ", image_name)

                if id > 0:
                    logger.info("Deleting disk: {} has been started as a job".format(image_name))
                return id

            except Exception as ex:
                logger.error("Error Deleting disk: {}".format(image_name))
                # end: delete disk as a job #

        else:
            return StopDiskStatus.error

    def is_disk_deleting(self, id):
        jm = JobManager()
        return jm.is_done(id)

    # ***************************************************
    #                 Attach
    # ***************************************************

    def attach_disk(self, disk_meta, manual_ips, path_type, paths_count, auth_auto, auto_ip, pool):

        """

        :type disk_meta: DiskMeta
        """
        mange_config = ManageConfig()
        paths_list = []
        do_rename = False
        none_petasan_image = ""
        try:
            if not disk_meta.disk_name or not disk_meta.size or type(disk_meta.size) != int:
                return ManageDiskStatus.data_missing
            elif not auth_auto and (not disk_meta.user or not disk_meta.password):
                return ManageDiskStatus.data_missing
            elif not auto_ip and int(paths_count) > 2:
                return ManageDiskStatus.wrong_data
            elif not auto_ip and int(paths_count) != len(manual_ips):
                return ManageDiskStatus.wrong_data
            elif not auto_ip:
                ip_status = mange_config.validate_new_iscsi_ips(manual_ips, path_type)
                if ip_status == NewIPValidation.valid:
                    for ip in manual_ips:
                        paths_list.append(mange_config.get_path(ip))
                elif ip_status == NewIPValidation.used_already:
                    return ManageDiskStatus.used_already
                elif ip_status == NewIPValidation.wrong_subnet:
                    return ManageDiskStatus.wrong_subnet
            elif auto_ip:
                paths_list.extend(mange_config.get_new_iscsi_ips(path_type, paths_count))

            if not paths_list or len(paths_list) == 0:
                return ManageDiskStatus.ip_out_of_range

            ceph_api = CephAPI()
            consul_api = ConsulAPI()
            image_name_prefix = ConfigAPI().get_image_name_prefix()
            if not "".join([image_name_prefix, str(disk_meta.id)]) in ceph_api.get_rbd_images(pool):
                new_id = self.__get_next_disk_id()
                if ceph_api.is_image_busy(disk_meta.id, pool):
                    return ManageDiskStatus.is_busy
                do_rename = True
                none_petasan_image = disk_meta.id
                disk_meta.id = new_id

            disk_meta.pool = pool
            disk_meta.iqn = ":".join([mange_config.get_iqn_base(), disk_meta.id])
            disk_meta.paths = paths_list
            if auth_auto:
                disk_meta.user = ""
                disk_meta.password = ""
            disk_meta.wwn = self.__get_wwn(disk_meta.id)

            status = consul_api.find_disk(disk_meta.id)
            if status is not None:
                return ManageDiskStatus.disk_exists  # disk is running and attached
            else:
                if do_rename:
                    ceph_api.rename_image_to_petasan_index(none_petasan_image, image_name_prefix + new_id, pool)
                status = ceph_api.add_disk(disk_meta, False, pool)
                if status == ManageDiskStatus.done:
                    consul_api.add_disk_resource(disk_meta.id, "disk")
                    i = 0
                    for p in paths_list:
                        i += 1
                        consul_api.add_disk_resource("/".join(["", disk_meta.id, str(i)]), None)
                else:
                    if do_rename:
                        ceph_api.rename_image_to_petasan_index(image_name_prefix + new_id, none_petasan_image, pool)

        except DiskListException as e:
            status = ManageDiskStatus.disk_get__list_error
            logger.exception(e.message)
        except Exception as e:
            status = ManageDiskStatus.error
            logger.exception(e.message)
        return status

    # ***************************************************
    #                 Detach
    # ***************************************************

    def detach_disk(self, disk_id, pool):
        ceph_api = CephAPI()
        disk_meta = DiskMeta()
        disk_meta.id = disk_id
        disk_meta.disk_name = None

        return ceph_api.add_disk(disk_meta, False, pool)

    # ***************************************************
    #                 Edit
    # ***************************************************

    def edit_disk(self, disk_meta, auth_auto, pool):

        """

        :type disk_meta: DiskMeta
        """
        try:
            if not disk_meta.id or not disk_meta.disk_name or not disk_meta.size or type(disk_meta.size) != int:
                return ManageDiskStatus.data_missing
            elif not auth_auto and (not disk_meta.user or not disk_meta.password):
                return ManageDiskStatus.data_missing

            old_disk_meta = self.get_disk(disk_meta.id, pool)

            disk_meta.paths = old_disk_meta.paths
            disk_meta.iqn = old_disk_meta.iqn

            disk_meta.pool = pool

            ceph_api = CephAPI()

            if auth_auto:
                disk_meta.user = ""
                disk_meta.password = ""

            consul_api = ConsulAPI()
            status = consul_api.find_disk(disk_meta.id)

            if status is not None:
                return ManageDiskStatus.disk_exists  # disk is running and attached
            else:
                status = ceph_api.add_disk(disk_meta, False, pool)

        except DiskListException as e:
            status = ManageDiskStatus.disk_get__list_error
            logger.exception(e.message)
        except Exception as e:
            status = ManageDiskStatus.error
            logger.exception(e.message)
        return status

    # ***************************************************
    #                 Cluster Status
    # ***************************************************

    def get_cluster_disk_status(self):
        return CephAPI().get_ceph_cluster_status()

    """
    def get_available_space_kb(self):
        ceph_api = CephAPI()
        return ceph_api.get_available_space_kb()

    """

    # ***************************************************
    #                 Pools
    # ***************************************************

    def get_pools_info(self):
        ceph_api = CephAPI()
        pools_info = ceph_api.get_pools_info()
        return pools_info

    # ***************************************************
    #                 Private Helpers
    # ***************************************************

    def __get_wwn(self, disk_id):
        wwn = disk_id
        app_config = ConfigAPI().read_app_config()
        if app_config.wwn_fsid_tag:
            logger.info('include_wwn_fsid_tag() is true')
            fsid = ceph_disk.get_fsid(configuration().get_cluster_name())
            fsid_split = fsid[:8]
            wwn = fsid_split + disk_id
        logger.info('add disk wwn is ' + wwn)
        return wwn

    def __get_next_disk_id(self):
        ceph_api = CephAPI()
        """
        pools = ceph_api.get_pools_info()
        ids = []
        for pool in pools:
            if not ceph_api.is_active_pool(pool.name) :
                continue
        """
        ids = []
        pools = ceph_api.get_active_pools()
        for pool in pools:
            pool_ids = ceph_api.get_disks_meta_ids(pool)
            ids.extend(pool_ids)

        consul_api = ConsulAPI()
        consul_disk_ids = consul_api.get_disk_pools().keys()
        ids.extend(consul_disk_ids)

        new_id = get_next_id(ids, 5)
        return new_id

    def get_disks_meta_by_pool(self, pool_name):
        ceph_api = CephAPI()
        disks_meta = ceph_api.get_disks_meta_for_pool(pool_name)
        return disks_meta
