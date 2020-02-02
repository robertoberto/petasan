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
import math
import subprocess
import rbd
import rados
import datetime
from time import sleep
from PetaSAN.core.ceph.ceph_authenticator import CephAuthenticator
from PetaSAN.core.ceph.ceph_connector import CephConnector
from PetaSAN.core.ceph.meta_reader import Meta_Reader
from PetaSAN.core.ceph.mt_meta_reader import *
from PetaSAN.core.ceph.crush_map import *
from PetaSAN.core.ceph.replication.snapshots import Snapshots
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.entity.benchmark import RadosResult
from PetaSAN.core.entity.disk_info import DiskMeta
from PetaSAN.core.entity.models.ec_profile import ECProfile
from PetaSAN.core.entity.models.pool_info import PoolInfo
from PetaSAN.core.entity.maintenance import MaintenanceConfig
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.common.enums import ManageDiskStatus, Status, REPLICASSAVESTATUS, MaintenanceConfigState
from PetaSAN.core.common import cmd
from PetaSAN.core.ceph.replication.users import Users
from PetaSAN.core.common.cmd import call_cmd, exec_command, exec_command_ex
from PetaSAN.core.common.log import logger
from PetaSAN.core.common.CustomException import MetadataException, DiskListException, CephException, \
    PoolException, ECProfileException


# from PetaSAN.core.config.app_conf import get_image_prfix


class CephAPI:
    conf_api = ConfigAPI()

    def __init__(self):
        pass

    def connect(self):

        ceph_connector = CephConnector()
        return ceph_connector.connect()

    # ################################################################################################################ #
    #                                                  Disk Operations                                                 #
    # ################################################################################################################ #

    def add_disk(self, disk_meta, create_disk, pool,
                 cureate_date=datetime.now()):
        """

        :type disk_meta: DiskMeta
        """
        status = ManageDiskStatus.error
        cluster = self.connect()
        disk = DiskMeta()
        if cluster != -1:

            try:
                io_ctx = cluster.open_ioctx(pool)
                status = 0
                rbd_inst = rbd.RBD()
                disk_metas = self.get_disks_meta()
                disk_name_is_exists = False

                for i in disk_metas:
                    if i.disk_name == disk_meta.disk_name:
                        disk_name_is_exists = True
                        break
                if create_disk:
                    size = disk_meta.size * 1024 ** 3
                    if disk_name_is_exists:
                        status = ManageDiskStatus.disk_name_exists

                    if status != ManageDiskStatus.disk_name_exists:
                        rbd_inst.create(io_ctx, self.conf_api.get_image_name_prefix() + disk_meta.id, size,
                                        old_format=False, data_pool=disk_meta.data_pool)
                        logger.info("Disk %s created" % disk_meta.disk_name)
                        status = ManageDiskStatus.done_metaNo
                if not create_disk:
                    try:
                        attr = self.read_image_metadata(self.conf_api.get_image_name_prefix() + disk_meta.id, pool)
                        petasan = attr.get(self.conf_api.get_image_meta_key())
                        if petasan:
                            disk.load_json(petasan)
                    except:
                        pass

                    if disk_meta.disk_name is not None and disk_meta.disk_name != disk.disk_name and disk_name_is_exists:
                        status = ManageDiskStatus.disk_name_exists

                if (
                                status == ManageDiskStatus.done_metaNo or not create_disk) and status != ManageDiskStatus.disk_name_exists:
                    attr_object = self.__get_header_object(self.conf_api.get_image_name_prefix() + disk_meta.id, pool)

                    if create_disk:
                        disk.id = disk_meta.id
                        disk.disk_name = disk_meta.disk_name
                        disk.size = disk_meta.size
                        disk.create_date = str(cureate_date.date())

                    else:  # edit or attach or detach
                        if not disk.id or len(disk.id) == 0:
                            # attach first time non-PetaSAN disk
                            disk.id = disk_meta.id
                        if disk_meta.disk_name is not None:  # edit and attach prev PetaSAN disk
                            disk.disk_name = disk_meta.disk_name
                        else:  # detach
                            # disk.disk_name = ""
                            disk_meta.data_pool = disk.data_pool

                        if disk_meta.size is not None:  # edit and attach
                            if disk_meta.size > disk.size:
                                size = disk_meta.size * 1024 ** 3
                                rbd.Image(io_ctx, str(self.conf_api.get_image_name_prefix() + disk_meta.id)).resize(
                                    size)
                                disk.size = disk_meta.size

                    disk.acl = disk_meta.acl
                    disk.user = disk_meta.user
                    disk.password = disk_meta.password
                    disk.iqn = disk_meta.iqn
                    disk.pool = disk_meta.pool
                    disk.paths = disk_meta.paths
                    disk.wwn = disk_meta.wwn
                    disk.data_pool = disk_meta.data_pool
                    disk.is_replication_target = disk_meta.is_replication_target
                    io_ctx.set_xattr(str(attr_object), str(self.conf_api.get_image_meta_key()), disk.write_json())
                    status = ManageDiskStatus.done
                io_ctx.close()

            except MetadataException as e:
                status = ManageDiskStatus.disk_meta_cant_read
            except DiskListException as e:
                status = ManageDiskStatus.disk_get__list_error
                logger.exception(e.message)
            except rbd.ImageExists as e:
                logger.error("Error while creating image, image %s already exists." % disk_meta.id)
                status = ManageDiskStatus.disk_exists
            except Exception as e:
                if status == -1:
                    logger.error("Error while creating image %s, cannot connect to cluster." % disk_meta.disk_name)
                elif status == 2:
                    logger.error(
                        "Error while creating image %s, could not add metadata." % disk_meta.id)
                elif status == 1:
                    logger.warning(
                        "Error while creating image %s, connection not closed" % disk_meta.id)

                logger.exception(e.message)

            cluster.shutdown()
            return status
        else:
            return -1

    def delete_disk(self, disk_id, pool):
        cluster = self.connect()
        ioctx = None

        try:
            ioctx = cluster.open_ioctx(pool)
            try:
                rbd_inst = rbd.RBD()
                if not "".join([self.conf_api.get_image_name_prefix(), str(disk_id)]) in self.get_rbd_images(pool):
                    rbd_inst.remove(ioctx, str(disk_id))
                else:
                    rbd_inst.remove(ioctx, "".join([str(self.conf_api.get_image_name_prefix()), str(disk_id)]))
                status = Status.done
            except Exception as e:
                logger.error("Delete disk %s error" % disk_id)
                logger.exception(e.message)
                status = Status.error

        except Exception as e:
            logger.error("Delete disk %s error" % disk_id)
            logger.exception(e.message)
            status = Status.error

        ioctx.close()
        cluster.shutdown()

        return status

    # ################################################################################################################ #
    #                                                  Cluster Health                                                  #
    # ################################################################################################################ #

    def get_ceph_cluster_status(self):
        cluster = self.connect()
        if cluster != -1:
            try:
                out, buf, err = cluster.mon_command(json.dumps({'prefix': 'status', 'format': "json"}), '', timeout=5)
                cluster.shutdown()
                if len(err) > 0:
                    return None
                return buf
            except Exception as e:
                # logger.exception(e.message)
                cluster.shutdown()
                raise MetadataException("Cannot get ceph cluster status.")

        return None

    def is_health_ok(self):
        health = self.get_health()
        if health is None:
            return False
        if health == 'HEALTH_OK':
            return True
        return None

    def get_health(self):
        try:
            cluster_status = self.get_ceph_cluster_status()
            if cluster_status is not None:
                cluster_status = json.loads(cluster_status)

                if 'health' not in cluster_status:
                    return None
                health = cluster_status['health']
                if health is None or len(health) == 0:
                    return None

                if 'overall_status' in health:
                    return health['overall_status']

                if 'status' in health:
                    return health['status']

        except:
            logger.exception("Error occur during get_health")
        return None

    # ################################################################################################################ #
    #                                                    Benchmark                                                     #
    # ################################################################################################################ #

    def create_rados_test_pool(self):
        cluster_name = configuration().get_cluster_name()
        self.delete_rados_test_pool()
        call_cmd('ceph osd pool create petasan_benchmark 256 256 --cluster {}'.format(cluster_name))

    def delete_rados_test_pool(self):
        cluster_name = configuration().get_cluster_name()
        call_cmd(
            'ceph osd pool delete petasan_benchmark petasan_benchmark --yes-i-really-really-mean-it --cluster {}'.format(
                cluster_name))

    def rados_write(self, duration, threads, block_size_type, pool):
        call_cmd("sync")
        call_cmd("echo 3| tee /proc/sys/vm/drop_caches &&  sync")
        cluster_name = configuration().get_cluster_name()
        """
        out, err = exec_command(
            'rados bench -p petasan_benchmark {_duration} write -t {_threads} -b {_rados_size_type} --no-cleanup --cluster {_cluster_name}'.format(
                _duration=duration, _threads=threads,
                _rados_size_type=block_size_type,_cluster_name=cluster_name))
        """
        out, err = exec_command(
            'rados bench -p {_pool} {_duration} write -t {_threads} -b {_rados_size_type} --no-cleanup --cluster {_cluster_name}'.format(
                _pool=pool, _duration=duration, _threads=threads,
                _rados_size_type=block_size_type, _cluster_name=cluster_name))

        rs = RadosResult()
        for line in out.splitlines():
            rs.node_name = configuration().get_node_name()
            if line.startswith("Average IOPS"):
                rs.iops = int(line.split(":")[1])
            elif line.startswith("Bandwidth"):
                rs.throughput = float(line.split(":")[1])

        return rs

    def rados_read(self, duration, threads, pool):
        call_cmd("sync")
        call_cmd("echo 3| tee /proc/sys/vm/drop_caches &&  sync")
        cluster_name = configuration().get_cluster_name()

        """
        out, err = exec_command(
            'rados bench -p petasan_benchmark {_duration} rand -t {_threads} --cluster {_cluster_name}'.format(
                _duration=duration, _threads=threads,_cluster_name=cluster_name))
        """
        out, err = exec_command(
            'rados bench -p {_pool} {_duration} rand -t {_threads} --cluster {_cluster_name}'.format(
                _pool=pool, _duration=duration, _threads=threads, _cluster_name=cluster_name))

        rs = RadosResult()
        for line in out.splitlines():
            rs.node_name = configuration().get_node_name()
            if line.startswith("Average IOPS"):
                rs.iops = int(line.split(":")[1])
            elif line.startswith("Bandwidth"):
                rs.throughput = float(line.split(":")[1])

        return rs

    def rados_benchmark_clean(self, pool):
        cluster_name = configuration().get_cluster_name()
        call_cmd('rados cleanup -p {} --cluster {}'.format(pool, cluster_name))

    # ################################################################################################################ #
    #                                                    Maintenance                                                   #
    # ################################################################################################################ #

    def get_maintenance_setting(self):
        cluster_name = configuration().get_cluster_name()
        out, err = exec_command("ceph osd dump --cluster {} | grep flags".format(cluster_name))
        out = str(out)

        config = MaintenanceConfig()

        if out.find("nobackfill") == -1:
            config.osd_backfill = MaintenanceConfigState.on
        else:
            config.osd_backfill = MaintenanceConfigState.off

        if out.find("nodeep-scrub") == -1:
            config.osd_deep_scrub = MaintenanceConfigState.on
        else:
            config.osd_deep_scrub = MaintenanceConfigState.off

        if out.find("nodown") == -1:
            config.osd_down = MaintenanceConfigState.on
        else:
            config.osd_down = MaintenanceConfigState.off

        if out.find("noout") == -1:
            config.osd_out = MaintenanceConfigState.on
        else:
            config.osd_out = MaintenanceConfigState.off

        # if out.find("pause") == -1:
        #     config.osd_pause = MaintenanceConfigState.on
        # else:
        #     config.osd_pause = MaintenanceConfigState.off


        if out.find("norebalance") == -1:
            config.osd_rebalance = MaintenanceConfigState.on
        else:
            config.osd_rebalance = MaintenanceConfigState.off

        if out.find("norecover") == -1:
            config.osd_recover = MaintenanceConfigState.on
        else:
            config.osd_recover = MaintenanceConfigState.off

        if out.find("noscrub") == -1:
            config.osd_scrub = MaintenanceConfigState.on
        else:
            config.osd_scrub = MaintenanceConfigState.off

        return config

    def set_maintenance_setting(self, config):
        cluster_name = configuration().get_cluster_name()
        if config.osd_backfill == MaintenanceConfigState.on:
            call_cmd("ceph osd unset nobackfill --cluster {}".format(cluster_name))
        else:
            call_cmd("ceph osd set nobackfill --cluster {}".format(cluster_name))

        if config.osd_deep_scrub == MaintenanceConfigState.on:
            call_cmd("ceph osd unset nodeep-scrub --cluster {}".format(cluster_name))
        else:
            call_cmd("ceph osd set nodeep-scrub --cluster {}".format(cluster_name))

        if config.osd_down == MaintenanceConfigState.on:
            call_cmd("ceph osd unset nodown --cluster {}".format(cluster_name))
        else:
            call_cmd("ceph osd set nodown --cluster {}".format(cluster_name))

        if config.osd_out == MaintenanceConfigState.on:
            call_cmd("ceph osd unset noout --cluster {}".format(cluster_name))
        else:
            call_cmd("ceph osd set noout --cluster {}".format(cluster_name))

        # if config.osd_pause == MaintenanceConfigState.on:
        #     call_cmd("ceph osd unset pause")
        # else:
        #     call_cmd("ceph osd set pause")

        if config.osd_rebalance == MaintenanceConfigState.on:
            call_cmd("ceph osd unset norebalance --cluster {}".format(cluster_name))
        else:
            call_cmd("ceph osd set norebalance --cluster {}".format(cluster_name))

        if config.osd_recover == MaintenanceConfigState.on:
            call_cmd("ceph osd unset norecover --cluster {}".format(cluster_name))
        else:
            call_cmd("ceph osd set norecover --cluster {}".format(cluster_name))

        if config.osd_scrub == MaintenanceConfigState.on:
            call_cmd("ceph osd unset noscrub --cluster {}".format(cluster_name))
        else:
            call_cmd("ceph osd set noscrub --cluster {}".format(cluster_name))

    def set_backfill_speed(self, backfill_speed):
        cluster_name = configuration().get_cluster_name()
        if backfill_speed == 1:
            logger.info('backfill_speed choice : very slow')
            ret1, stdout1, stderr1 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_max_backfills 1' --cluster " + cluster_name)
            ret2, stdout2, stderr2 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_recovery_max_active 1' --cluster " + cluster_name)
            ret3, stdout3, stderr3 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_recovery_sleep 2' --cluster " + cluster_name)
            logger.info('Done changing backfill speed to very slow ...')

        elif backfill_speed == 2:
            logger.info('backfill_speed choice : slow')
            ret1, stdout1, stderr1 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_max_backfills 1' --cluster " + cluster_name)
            ret2, stdout2, stderr2 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_recovery_max_active 1' --cluster " + cluster_name)
            ret3, stdout3, stderr3 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_recovery_sleep 0.7' --cluster " + cluster_name)
            logger.info('Done changing backfill speed to slow ...')

        elif backfill_speed == 3:
            logger.info('backfill_speed choice : medium')
            ret1, stdout1, stderr1 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_max_backfills 1' --cluster " + cluster_name)
            ret2, stdout2, stderr2 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_recovery_max_active 1' --cluster " + cluster_name)
            ret3, stdout3, stderr3 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_recovery_sleep 0' --cluster " + cluster_name)
            logger.info('Done changing backfill speed to medium ...')

        elif backfill_speed == 4:
            logger.info('backfill_speed choice : fast')
            ret1, stdout1, stderr1 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_max_backfills 5' --cluster " + cluster_name)
            ret2, stdout2, stderr2 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_recovery_max_active 3' --cluster " + cluster_name)
            ret3, stdout3, stderr3 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_recovery_sleep 0' --cluster " + cluster_name)
            logger.info('Done changing backfill speed to fast ...')

        elif backfill_speed == 5:
            logger.info('backfill_speed choice : very fast')
            ret1, stdout1, stderr1 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_max_backfills 7' --cluster " + cluster_name)
            ret2, stdout2, stderr2 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_recovery_max_active 7' --cluster " + cluster_name)
            ret3, stdout3, stderr3 = exec_command_ex(
                "ceph tell osd.* injectargs '--osd_recovery_sleep 0' --cluster " + cluster_name)
            logger.info('Done changing backfill speed to very fast ...')

        else:
            logger.error("error : failed to set speed value : No such value {}".format(backfill_speed))

    # ################################################################################################################ #
    #                                               Metadata Operations                                                #
    # ################################################################################################################ #

    # Given disk id and pool name , Returns DiskMeta Object for specific image

    def get_disk_meta(self, disk_id, pool):
        disk = DiskMeta()
        try:
            # if there are rbd images created outside petasan and we need to support, images must not start with image-.
            if not "".join([self.conf_api.get_image_name_prefix(), disk_id]) in self.get_rbd_images(pool):
                disk.id = disk_id
                disk.disk_name = disk_id
                disk.size = self.__get_image_size(disk_id, pool)
                disk.is_petasan_image = False
                disk.pool = pool
                disk.data_pool = self.get_image_data_pool(disk.pool, disk.disk_name)

            else:
                # Petasan rbd images must start with 'image-'.
                attr = self.read_image_metadata("".join([self.conf_api.get_image_name_prefix(), disk_id]), pool)
                meta = attr.get(self.conf_api.get_image_meta_key())
                disk = DiskMeta()
                if meta:
                    disk.load_json(meta)
                    disk.is_petasan_image = True
                    disk.pool = pool

                else:
                    disk = None

            return disk
        except Exception as e:
            logger.exception(e.message)
            raise DiskListException(DiskListException.DISK_NOT_FOUND,"Cannot get disk meta.")

        return None

    # Given image Name, Returns xattrs dictionary on object header
    def read_image_metadata(self, image, pool):
        cluster = self.connect()
        params = {}
        if cluster != -1:

            try:
                io_ctx = cluster.open_ioctx(pool)
                meta_object = self.__get_header_object(image, pool)
                meta_reader = Meta_Reader()
                params = meta_reader.read_image_metadata(io_ctx, meta_object)
                io_ctx.close()
                cluster.shutdown()

            except Exception as e:
                cluster.shutdown()
                raise MetadataException("Cannot get metadata.")

        return params

    # Returns rbd header object
    def __get_header_object(self, image, pool):
        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        config = configuration()
        cluster_name = config.get_cluster_name()

        try:
            cmd = "rbd info " + pool + "/" + str(image) + " " + ceph_auth.get_authentication_string() + " --cluster " + cluster_name + " | grep rbd_data"
            ret, stdout, stderr = exec_command_ex(cmd)

            if ret != 0:
                if stderr:
                    raise MetadataException("Cannot get image meta object from rbd header.")

            rbd_data = stdout.rstrip().strip()
            dot_indx = rbd_data.rfind(".")

            image_id = rbd_data[(dot_indx+1):]

            meta_object = "rbd_header." + image_id

            return meta_object

        except Exception as e:
            raise MetadataException("Cannot get image meta object from rbd header.")

    # Returns DiskMeta Objects for all images
    def get_disks_meta(self):
        disks = []
        try:
            """
            pools_info = self.get_pools_info()
            for pool in pools_info:
                if not self.is_active_pool(pool.name):
                    continue
            """
            pools = self.get_active_pools()
            for pool in pools:
                pool_disks = self.get_disks_meta_for_pool(pool)
                disks.extend(pool_disks)
        except Exception as e:
            logger.exception(e.message)
            raise Exception("Error getting disk metas, cannot open connection.")
        return disks

    def get_disks_meta_for_pool(self, pool):
        disks = []
        try:
            image_metada = read_meta(pool)
            for image, meta in image_metada.iteritems():
                if meta:
                    disk = DiskMeta()
                    disk.load_json(meta)
                    disk.is_petasan_image = True
                    disk.pool = pool
                    disks.append(disk)
                else:
                    disk = DiskMeta()
                    disk.id = image
                    disk.size = self.__get_image_size(image, pool)
                    disk.is_petasan_image = False
                    disk.pool = pool
                    disk.data_pool = self.get_image_data_pool(disk.pool, disk.id)
                    disks.append(disk)
        except Exception as e:
            logger.exception(e.message)
            raise Exception("Error getting disk metas for pool, cannot open connection.")
        return disks

    def get_image_data_pool(self, pool, image_name):
        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        config = configuration()
        cluster_name = config.get_cluster_name()
        cmd = 'rbd -p {} info {} {} --cluster {} | grep data_pool | cut -d : -f2'.format(pool, image_name,
                                                                                         ceph_auth.get_authentication_string(),
                                                                                         cluster_name)
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        data_pool = stdout.replace(" ", "")
        return data_pool

    def get_disks_meta_ids(self, pool):
        try:
            ids = []
            image_metada = read_meta(pool)
            for image, meta in image_metada.iteritems():
                if meta:
                    disk = DiskMeta()
                    disk.load_json(meta)
                    ids.append(disk.id)

            return ids

        except Exception as e:
            logger.exception(e.message)
            raise Exception("Error getting disks metas.")

        return None

    # Given only disk id, Returns DiskMeta Object for specific image
    def get_diskmeta(self, disk_id):
        pool = self.get_pool_bydisk(disk_id)  # get pool by disk_id
        if pool is None:
            raise PoolException(PoolException.CANNOT_GET_POOL, "Cannot get pool of disk " + str(disk_id))

        try:
            disk_metadata = self.get_disk_meta(disk_id, pool)  # get disk entity by disk_id and pool_name
            return disk_metadata

        except PoolException as e:
            raise PoolException(PoolException.CANNOT_GET_POOL, "Cannot get disk meta.")

        except DiskListException as e:
            raise DiskListException(DiskListException.DISK_NOT_FOUND, "Cannot get disk meta.")

        except CephException as e:
            raise CephException(CephException.GENERAL_EXCEPTION, "Cannot get disk meta.")

        except MetadataException as e:
            raise MetadataException("Cannot get disk meta.")

        except Exception as e:
            raise Exception("Cannot get disk meta.")

    # ################################################################################################################ #
    #                                                 Image Operations                                                 #
    # ################################################################################################################ #

    def get_rbd_images(self, pool):
        cluster = self.connect()
        if cluster != -1:
            try:
                io_ctx = cluster.open_ioctx(pool)
                try:
                    rbd_inst = rbd.RBD()
                    ls = rbd_inst.list(io_ctx)
                    io_ctx.close()
                    cluster.shutdown()
                    return ls
                except Exception as e:
                    logger.exception(e.message)
                    io_ctx.close()
                    cluster.shutdown()
                return None

            except Exception as e:
                logger.exception(e.message)
                cluster.shutdown()
                raise Exception("Error getting disks ids from rbd, cannot open connection.")

        cluster.shutdown()
        return None

    """
    def get_available_space_kb(self):

        cluster = self.connect()
        size = None
        if cluster != -1:
            cluster.shutdown()
            size = cluster.get_cluster_stats()['kb_avail']

        cluster.shutdown()
        return size
    """

    def __get_image_size(self, image, pool):
        cluster = self.connect()
        size = 0
        if cluster == -1:
            cluster.shutdown()
            return size

        try:
            ioctx = cluster.open_ioctx(pool)
            size = int(math.ceil(float(rbd.Image(ioctx, image).size()) / float(1024 ** 3)))
            ioctx.close()

        except Exception as e:
            logger.error("Get ceph image size %s error" % image)
            logger.exception(e.message)
            size = 0

        cluster.shutdown()
        return size

    def is_image_busy(self, image, pool):
        cluster_name = configuration().get_cluster_name()
        meta_object = self.__get_header_object(image, pool)
        p = subprocess.Popen(["rados", "listwatchers", "--cluster", cluster_name, "--pool", pool, meta_object],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.stdout.read()
        if out:
            logger.debug("Disk {} is busy.".format(image))
            return True
        return False

    def rename_image_to_petasan_index(self, image, new_index, pool):
        cluster = self.connect()
        size = 0
        try:
            ioctx = cluster.open_ioctx(pool)
            try:

                rbd_inst = rbd.RBD()
                rbd_inst.rename(ioctx, image, new_index)
                ioctx.close()
                cluster.shutdown()

            except Exception as e:
                logger.error("Convert image  %s error." % image)
                logger.exception(e.message)
                ioctx.close()
                cluster.shutdown()
                raise Exception("Convert image  %s error." % image)

        except Exception as e:
            logger.exception(e.message)
            cluster.shutdown()
            raise Exception("Convert image: connection Error.")

    # ################################################################################################################ #
    #                                                  Image Mapping                                                   #
    # ################################################################################################################ #

    def map_iamge(self, image, pool):
        cluster_name = configuration().get_cluster_name()
        p = subprocess.Popen("rbd --cluster {} map --image ".format(cluster_name) + pool + "/" + image, shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        err = p.stderr.read()
        if err.find("resource busy") != -1:
            logger.error("Cannot map image %s. resource is busy." % image)
            return Status.error  # busy
        elif str(err).find("Warning") == -1 and len(err) != 0:
            logger.errord("map error is {}".format(err))
            logger.error("Cannot map image %s. error. " % image)
            return Status.error  # errord
        else:
            logger.info("Image %s mapped successfully." % image)
            return Status.done  # done

    """
    def unmap_image(self, disk_id, pool):
        cluster_name = configuration().get_cluster_name()
        p = subprocess.Popen("rbd --cluster {} unmap ".format(cluster_name)+ "/dev/rbd/" + str(pool) + "/" + str(disk_id),shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        err = p.stderr.read()
        if err.find("resource busy") != -1:
            logger.error("Cannot unmap image %s. resource is busy." % disk_id)
            return Status.error  # busy
        elif str(err).find("Warning") ==-1 and len(err) != 0:
            logger.error("Cannot unmap image %s. error. " % disk_id)
            return Status.error  # error
        else:
            logger.info("Image %s unmapped successfully." % disk_id)
            return Status.done  # done
    """

    def unmap_image(self, image):
        import os
        path = '/dev/rbd/'
        pools = []
        cluster_name = configuration().get_cluster_name()

        if not os.path.isdir(path):
            logger.error("Cannot unmap image %s. error, no mapped images found. " % image)
            return Status.error

        for f in os.listdir(path):
            if os.path.isdir(path + f):
                pools.append(f)

        for pool in pools:
            for f in os.listdir(path + pool):
                # if f.startswith(image) :
                if f == image:
                    cmd = 'rbd unmap ' + path + pool + '/' + image + ' --cluster ' + cluster_name
                    ret, stdout, stderr = exec_command_ex(cmd)
                    if ret == 0:
                        logger.info("Image %s unmapped successfully." % image)
                        return Status.done
                    if stderr:
                        if stderr.find("resource busy") != -1:
                            logger.error("Cannot unmap image %s. resource is busy." % image)
                            return Status.error

                    logger.error("Cannot unmap image %s. error. " % image)
                    return Status.error

        logger.error("Cannot unmap image %s. error, no mapped images found. " % image)
        return Status.error

    def get_mapped_images(self):
        cluster_name = configuration().get_cluster_name()
        cmd = 'rbd showmapped --format json --cluster {}'.format(cluster_name)

        try:
            ret, out, err = exec_command_ex(cmd)
            if err:
                logger.error("Error executing cmd : {} , {}".format(cmd , str(err)))
                return None

            """
            images = dict()
            for line in str(out).splitlines():
                id, pool, image, snap, device = line.replace("\s+", "").split()
                if id == "id":
                    continue

                count = images.get(image, 0) + 1
                images[image] = count
            return images
            """

            images = dict()
            image = ""
            mapped_images = json.loads(out)

            # Ceph 12 :
            if isinstance(mapped_images, dict):
                for key, value in mapped_images.iteritems():
                    if 'name' in value:
                        image = value['name']
                        count = images.get(image, 0) + 1
                        images[image] = count

            # Ceph 14 :
            elif isinstance(mapped_images, list):
                for mapped_images in mapped_images:
                    if 'name' in mapped_images:
                        image = mapped_images['name']
                        count = images.get(image, 0) + 1
                        images[image] = count

            return images

        except Exception as e:
            logger.error("Error executing cmd : {}".format(cmd))
            logger.exception(e.message)
            return None


    # ################################################################################################################ #
    #                                                 Crush Operations                                                 #
    # ################################################################################################################ #

    def get_bucket_types(self):
        crush = CrushMap()
        crush.read()
        return crush.get_bucket_types()

    def get_buckets(self):
        crush = CrushMap()
        crush.read()
        return crush.get_buckets()

    def save_buckets(self, buckets):
        crush = CrushMap()
        crush.read(True)
        crush.set_buckets(buckets)
        crush.write()

    def get_rules(self):
        crush = CrushMap()
        crush.read()
        return crush.get_rules()

    def get_next_rule_id(self):
        crush = CrushMap()
        crush.read()
        return crush.get_next_rule_id()

    def add_rule(self, name, body):
        crush = CrushMap()
        crush.read(True)
        crush.add_rule(name, body)
        crush.write()

    def update_rule(self, name, body):
        crush = CrushMap()
        crush.read(True)
        crush.update_rule(name, body)
        crush.write()

    def delete_rule(self, name):
        crush = CrushMap()
        crush.read(True)
        crush.delete_rule(name)
        crush.write()

    # ################################################################################################################ #
    #                                                      Pools                                                       #
    # ################################################################################################################ #


    def get_pools(self):
        pools = []
        cluster = self.connect()
        if cluster == -1:
            logger.error('get_pools Error')
            cluster.shutdown()
            raise Exception("Ceph Error.")
        try:
            pools = cluster.list_pools()
            cluster.shutdown()

        except Exception as e:
            logger.error('get_pools Error')
            cluster.shutdown()
            raise Exception("Ceph Error.")

        return pools

    """
    def is_active_pool(self,pool):
        pc = PoolChecker(pool)
        return pc.is_active()
    """

    def get_active_pools(self):

        cmd = ConfigAPI().get_active_pools_script()
        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            logger.error('Error getting active pools')
            return []

        active_pools = []
        try:
            active_pools = json.loads(stdout)
            return active_pools

        except Exception as e:
            logger.error('Error getting active pools, stdout:' + stdout)

        return []

    ## NEW ##
    def get_active_osds(self):

        cmd = ConfigAPI().get_active_osds_script()
        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            logger.error('Error getting active osds')
            return {}

        active_osds = {}
        try:
            active_osds = json.loads(stdout)
            return active_osds

        except Exception as e:
            logger.error('Error getting active osds, stdout:' + stdout)

        return {}

    def get_pool_bydisk(self, disk_id):
        try:
            image = self.conf_api.get_image_name_prefix() + disk_id
            """
            pools = self.get_pools()
            for pool in pools:
                if not self.is_active_pool(pool) :
                    continue
            """
            pools = self.get_active_pools()
            for pool in pools:
                images = self.get_rbd_images(pool)
                if images is None:
                    continue
                if image in images:
                    attr = self.read_image_metadata(image, pool)
                    if not attr:
                        continue
                    petasan_meta = attr.get(self.conf_api.get_image_meta_key())
                    if not petasan_meta:
                        continue
                    disk = DiskMeta()
                    disk.load_json(petasan_meta)
                    if disk.id == disk.id:
                        return pool

        except Exception as e:
            logger.error('get_pool_bydisk Exception')

        logger.error('get_pool_bydisk could not find pool for disk ' + disk_id)
        return None

    def get_pools_info(self):
        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        config = configuration()
        cluster_name = config.get_cluster_name()

        pools_info_rule_id = {}  # defined for pools info comes from cmd --> {pool_name:pool_info}
        pools = []  # defined for "PoolInfo" objects

        cmd = 'ceph osd dump --format json {} --cluster {}'.format(ceph_auth.get_authentication_string(), cluster_name)
        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr or 'error connecting' in stderr):
                logger.error('Error in Ceph Connection cmd:' + cmd)
                raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        # filling pools_info_rule_id :
        # ============================
        stdout_json = json.loads(stdout)
        for pool_info in stdout_json["pools"]:
            pools_info_rule_id.update({pool_info["pool_name"]: pool_info})

        # get rules :
        # ===========
        rules_info = self.get_rules()
        rule_name_by_id = {}  # defined for rules --> {rule_id:rule_name}

        for rule_name, rule_body in rules_info.iteritems():
            id_indx = rule_body.find("id")
            newline_indx = rule_body.find("\n", id_indx)

            if id_indx > 0 and newline_indx > 0:
                id = rule_body[id_indx + 2: newline_indx]
                rule_name_by_id.update({int(id): rule_name})

        # get active osds :
        # =================
        active_osds_info = {}  # defined for active_osds --> {pool_name:active_osds}
        active_osds_info = self.get_active_osds()


        # filling "pools" list by "PoolInfo" objects:
        # ===========================================
        for name, pool_body in pools_info_rule_id.iteritems():
            poolInfo = PoolInfo()
            rule_id = pool_body["crush_rule"]

            poolInfo.name = name

            if pool_body["type"] == 3:
                poolInfo.type = "erasure"
                poolInfo.ec_profile = pool_body["erasure_code_profile"]

            poolInfo.id = pool_body["pool"]
            poolInfo.pg_num = pool_body["pg_num"]
            poolInfo.pgp_num = pool_body["pg_placement_num"]
            poolInfo.min_size = pool_body["min_size"]
            poolInfo.size = pool_body["size"]
            poolInfo.rule_id = rule_id
            poolInfo.rule_name = rule_name_by_id[rule_id]

            if "compression_mode" in pool_body["options"]:
                poolInfo.compression_mode = pool_body["options"]["compression_mode"]
            if "compression_algorithm" in pool_body["options"]:
                poolInfo.compression_algorithm = pool_body["options"]["compression_algorithm"]

            if active_osds_info:
                # Check if current pool name exists in active_osds_info dictionary or not :
                if name in active_osds_info:
                    poolInfo.active_osds = active_osds_info[name]

                else:
                    poolInfo.active_osds = 0

            # pools_info.update({poolInfo.name : {"id" : poolInfo.id , "pg_num" : poolInfo.pg_num , "pgp_num" : poolInfo.pgp_num,
            # "replicated_min_size" : poolInfo.replica_min_size , "replicated_size" : poolInfo.replica_size,
            # "rule_id" : poolInfo.rule_id , "rule_name" : poolInfo.rule_name}})

            pools.append(poolInfo)

        return pools

    def add_pool(self, pool_info):

        config = configuration()
        cluster_name = config.get_cluster_name()
        error_msg = ''
        error = False

        cmd = 'ceph osd pool create {} {} {} {} {} {} --cluster {}'.format(pool_info.name, pool_info.pg_num,
                                                                           pool_info.pg_num, pool_info.type,
                                                                           pool_info.ec_profile, pool_info.rule_name,
                                                                           cluster_name)
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            if stderr:
                if 'Connection timed out' in stderr or 'error connecting' in stderr:
                    logger.error('Error in Ceph Connection cmd:' + cmd)
                    raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

                if 'already exists' in stderr:
                    logger.error('add pool failed, duplicate pool name: ' + pool_info.name)
                    raise PoolException(PoolException.DUPLICATE_NAME, 'Pool name already exists')

                if 'pool size is bigger than the crush rule max size' in stderr:
                    logger.error('add pool failed, duplicate pool name: ' + pool_info.name)
                    raise PoolException(PoolException.SIZE_TOO_LARGE, 'Pool size too large')

                if 'pool size is smaller than the crush rule min size' in stderr:
                    logger.error('add pool failed, duplicate pool name: ' + pool_info.name)
                    raise PoolException(PoolException.SIZE_TOO_SMALL, 'Pool size too small')

                if 'total pgs, which exceeds max' in stderr:
                    logger.error('add pool failed, duplicate pool name: ' + pool_info.name)
                    raise PoolException(PoolException.OSD_PGS_EXCEEDED, 'OSD PGs Exceeded')

                if 'pool size is bigger than the crush rule max size' in stderr:
                    error_msg += ':max size smaller than pool size '
                    error = True

                if 'pool size is smaller than the crush rule min size' in stderr:
                    error_msg += ':min size larger than pool size '
                    error = True

                if error:
                    raise PoolException(PoolException.PARAMETER_SET, error_msg)

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        cmd = 'ceph osd pool application enable {} rbd --cluster {}'.format(pool_info.name, cluster_name)
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            if stderr:
                if 'Connection timed out' in stderr or 'error connecting' in stderr:
                    logger.error('Error in Ceph Connection cmd:' + cmd)
                    raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        if pool_info.type == "erasure":
            cmd = 'ceph osd pool set {} allow_ec_overwrites true --cluster {}'.format(pool_info.name, cluster_name)
            ret, stdout, stderr = exec_command_ex(cmd)

            if ret != 0:
                if stderr:
                    if 'Connection timed out' in stderr or 'error connecting' in stderr:
                        logger.error('Error in Ceph Connection cmd:' + cmd)
                        raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

                logger.error('General error in Ceph cmd:' + cmd)
                raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        self.update_pool(pool_info, False)

    def update_pool(self, pool_info, edit=True):

        config = configuration()
        cluster_name = config.get_cluster_name()
        cmd_base = 'ceph osd pool set {} {} {} --cluster {}'
        error = False
        error_msg = ''

        # ---------- size ----------
        if pool_info.type == "replicated":
            cmd = cmd_base.format(pool_info.name, 'size', pool_info.size, cluster_name)
            """
            if not call_cmd(cmd) :
                logger.error('Failed to execute:' + cmd)
                error = True
                error_msg += 'Number of Replicas, '
            """
            ret, stdout, stderr = exec_command_ex(cmd)
            if ret != 0:
                logger.error('Failed to execute:' + cmd)
                error = True
                error_msg += 'Number of Replicas '

                if stderr and 'pool size is bigger than the crush rule max size' in stderr:
                    error_msg += ':is bigger than the crush rule max size '

                if stderr and 'pool size is smaller than the crush rule min size' in stderr:
                    error_msg += ':is smaller than the crush rule min size '

                if stderr and 'total pgs, which exceeds max' in stderr:
                    error_msg += ':PG count per OSD exceeded '

                error_msg += ','


        # ---------- min size ----------
        cmd = cmd_base.format(pool_info.name, 'min_size', pool_info.min_size, cluster_name)
        if not call_cmd(cmd):
            logger.error('Failed to execute:' + cmd)
            error = True
            error_msg += 'Minimum number of Replicas, '


        # ---------- compression mode ----------
        cmd = cmd_base.format(pool_info.name, 'compression_mode', pool_info.compression_mode, cluster_name)
        if not call_cmd(cmd):
            logger.error('Failed to execute: ' + cmd)
            error = True
            error_msg += 'Compression mode'

        # ---------- compression algorithm ----------
        cmd = cmd_base.format(pool_info.name, 'compression_algorithm', pool_info.compression_algorithm, cluster_name)
        if not call_cmd(cmd):
            logger.error('Failed to execute: ' + cmd)
            error = True
            error_msg += 'Compression algorithm'


        # ---------- rule name ----------
        if edit == True:
            cmd = cmd_base.format(pool_info.name, 'crush_rule', pool_info.rule_name, cluster_name)
            """
            if not call_cmd(cmd) :
                logger.error('Failed to execute:' + cmd)
                error = True
                error_msg += 'Rule Name, '
            """
            ret, stdout, stderr = exec_command_ex(cmd)
            if ret != 0:
                logger.error('Failed to execute:' + cmd)
                error = True
                error_msg += 'Rule '

                if stderr and 'pool size is bigger than the crush rule max size' in stderr:
                    error_msg += ':max size smaller than pool size '

                if stderr and 'pool size is smaller than the crush rule min size' in stderr:
                    error_msg += ':min size larger than pool size '

                error_msg += ','

            if error:
                raise PoolException(PoolException.PARAMETER_SET, error_msg)

    def delete_pool(self, pool_name):

        config = configuration()
        cluster_name = config.get_cluster_name()

        cmd = 'ceph osd pool delete {} {} --yes-i-really-really-mean-it --cluster {}'.format(pool_name, pool_name,
                                                                                             cluster_name)
        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                if 'Connection timed out' in stderr or 'error connecting' in stderr:
                    logger.error('Error in Ceph Connection cmd:' + cmd)
                    raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

    def get_replicas(self, pool):
        cluster_name = configuration().get_cluster_name()
        p = subprocess.Popen("ceph osd  pool get {} size  --cluster {}".format(pool, cluster_name), shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out = p.stdout.read()
        if str(out).startswith("size:"):
            return str(out).split(":")[1].strip()

        raise Exception("Can't read replicas.")

    def set_replicas(self, size, pool):
        cluster_name = configuration().get_cluster_name()

        if call_cmd("ceph osd  pool set {} size {} --cluster {}".format(pool, size, cluster_name)):
            logger.info("Pool size changed successfully to {}.".format(size))
            if call_cmd("ceph osd  pool set {} min_size {} --cluster {}".format(pool, int(size) - 1, cluster_name)):
                return REPLICASSAVESTATUS.done
            else:
                logger.warning("Cannot change pool min_size.")
                return REPLICASSAVESTATUS.min_size_wrn

        raise REPLICASSAVESTATUS.error

    # ################################################################################################################ #
    #                                                 Pool Compression                                                 #
    # ################################################################################################################ #

    def get_compression_mode(self, pool):
        cluster_name = configuration().get_cluster_name()
        try:
            ret, stdout, stderr = exec_command_ex(
                "ceph osd pool get {} compression_mode --cluster {}".format(pool, cluster_name))
            if ret == 0:
                return str(stdout)
            else:
                logger.warning("Error getting compression mode")
                raise Exception("Exception getting compression mode")
        except Exception:
            raise Exception("Exception getting compression mode")

    def get_compression_algorithm(self, pool):
        cluster_name = configuration().get_cluster_name()
        try:
            ret, stdout, stderr = exec_command_ex(
                "ceph osd pool get {} compression_algorithm --cluster {}".format(pool, cluster_name))
            if ret == 0:  # status code =0, mean success execute cmd and exit
                return str(stdout)
            else:
                logger.warning("Error getting compression algorithm")
        except Exception:
            raise Exception("Exception getting compression algorithm")

    def set_compression_algorithm(self, algorithm, pool):
        cluster_name = configuration().get_cluster_name()
        try:
            ret, stdout, stderr = exec_command_ex(
                "ceph osd pool set {} compression_algorithm {} --cluster {}".format(pool, algorithm, cluster_name))
            if ret == 0:
                logger.debug("Success setting compression algorithm")
            else:
                logger.warning("Error setting compression algorithm")
        except Exception:
            raise Exception("Exception setting compression algorithm")

    def set_compression_mode(self, mode, pool):
        cluster_name = configuration().get_cluster_name()
        try:
            ret, stdout, stderr = exec_command_ex(
                "ceph osd pool set {} compression_mode {} --cluster {}".format(pool, mode, cluster_name))
            if ret == 0:  # status code =0, mean success execute cmd and exit
                logger.debug("Success setting compression mode")
            else:
                logger.warning("Error setting compression mode")
        except Exception:
            raise Exception("Exception setting compression mode")

    def create_default_ec_profiles(self):
        cluster_name = configuration().get_cluster_name()
        call_cmd('ceph osd erasure-code-profile set ec-21-profile k=2 m=1 --cluster {}'.format(cluster_name))
        call_cmd('ceph osd erasure-code-profile set ec-32-profile k=3 m=2 --cluster {}'.format(cluster_name))
        call_cmd('ceph osd erasure-code-profile set ec-42-profile k=4 m=2 --cluster {}'.format(cluster_name))
        call_cmd('ceph osd erasure-code-profile set ec-62-profile k=6 m=2 --cluster {}'.format(cluster_name))
        call_cmd('ceph osd erasure-code-profile set ec-63-profile k=6 m=3 --cluster {}'.format(cluster_name))

    def get_ec_profiles(self):
        profiles_list = self._do_get_ec_profiles()
        if len(profiles_list) < 2:
            logger.info("Creating default EC profiles")
            self.create_default_ec_profiles()
            profiles_list = self._do_get_ec_profiles()

        return profiles_list

    def _do_get_ec_profiles(self):
        profiles_list = {}
        config = configuration()
        cluster_name = config.get_cluster_name()
        cmd = 'ceph osd dump --format json --cluster {}'.format(cluster_name)
        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr or 'error connecting' in stderr):
                logger.error('Error in Ceph Connection cmd:' + cmd)
                raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

        stdout_json = json.loads(stdout)

        if "erasure_code_profiles" in stdout_json.keys():
            for profile, profile_info in stdout_json["erasure_code_profiles"].iteritems():
                profileInfo = ECProfile()
                profileInfo.name = profile
                if 'k' in profile_info.keys():
                    profileInfo.k = profile_info['k']
                if 'm' in profile_info.keys():
                    profileInfo.m = profile_info['m']
                if 'plugin' in profile_info.keys():
                    profileInfo.plugin = profile_info['plugin']
                if 'technique' in profile_info.keys():
                    profileInfo.technique = profile_info['technique']
                if 'c' in profile_info.keys():
                    profileInfo.durability_estimator = profile_info['c']
                if 'l' in profile_info.keys():
                    profileInfo.locality = profile_info['l']
                if 'stripe_unit' in profile_info.keys():
                    profileInfo.strip_unit = profile_info['stripe_unit']
                if 'packetsize' in profile_info.keys():
                    profileInfo.packet_size = profile_info['packetsize']
                profiles_list.update({profileInfo.name: profileInfo})

            return profiles_list

    def delete_ec_profile(self, profile_name):
        config = configuration()
        cluster_name = config.get_cluster_name()
        cmd = 'ceph osd erasure-code-profile rm {} --cluster {}'.format(profile_name, cluster_name)
        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr or 'error connecting' in stderr):
                logger.error('Error in Ceph Connection cmd:' + cmd)
                raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

            if stderr and ('using the erasure code profile ' in stderr):
                logger.error('Error in deleting profile because it is in use ' + cmd)
                raise ECProfileException(ECProfileException.ECPROFILE_IN_USE, 'ProfileIsUsedInPool')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

    def add_ec_profile(self, profile_info):
        config = configuration()
        cluster_name = config.get_cluster_name()
        locality = ""
        durability_estimator = ""
        plugin = ""
        packet_size = ""
        strip_unit = ""
        technique = ""
        name = profile_info.name
        k = "k=" + str(profile_info.k)
        m = "m=" + str(profile_info.m)

        if profile_info.locality > -1:
            locality = "l=" + str(profile_info.locality)

        if profile_info.durability_estimator > -1:
            durability_estimator = "c=" + str(profile_info.durability_estimator)

        if profile_info.plugin is not None and profile_info.plugin != "":
            plugin = "plugin=" + profile_info.plugin

        if profile_info.packet_size > -1:
            packet_size = "packetsize=" + profile_info.packet_size

        if profile_info.strip_unit is not None and profile_info.strip_unit != "":
            strip_unit = "stripe_unit=" + profile_info.strip_unit

        if profile_info.technique is not None and profile_info.technique != "":
            technique = "technique=" + profile_info.technique

        cmd = 'ceph osd erasure-code-profile set {} {} {} {} {} {} {} {} {} --cluster {}'.format(name, plugin, k, m,
                                                                                                 locality,
                                                                                                 durability_estimator,
                                                                                                 strip_unit,
                                                                                                 packet_size, technique,
                                                                                                 cluster_name)

        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                if 'Connection timed out' in stderr or 'error connecting' in stderr:
                    logger.error('Error in Ceph Connection cmd:' + cmd)
                    raise CephException(CephException.CONNECTION_TIMEOUT, 'ConnectionTimeError')

                if 'override erasure code profile' in stderr:
                    logger.error('Error in adding erasure code profile because the profile is already exist ' + cmd)
                    raise ECProfileException(ECProfileException.DUPLICATE_ECPROFILE_NAME, 'ProfileIsAlreadyExist')

                if 'k + m must be a multiple of l' in stderr or 'k must be a multiple of (k + m) / l' in stderr:
                    logger.error('error is ' + stderr + '-----' + cmd)
                    raise ECProfileException(ECProfileException.WRONG_ECPROFILE_LOCALITY_VALUE,
                                             'k + m must be a multiple of l')

                if 'could not parse stripe_unit' in stderr or 'stripe_unit {} does not match ec profile alignment'.format(
                        profile_info.strip_unit) in stderr:
                    logger.error('error is ' + stderr + '--------' + cmd)
                    raise ECProfileException(ECProfileException.INVALID_STRIPE_UNIT_ARGUMENT,
                                             'invalid stripe_unit argument')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION, 'GeneralCephException')

    # ################################################################################################################ #
    #                                            Image Snapshots Operations                                            #
    # ################################################################################################################ #

    def get_disk_snapshots(self, pool_name, image_name):
        snapshot_obj = Snapshots()
        snaps_ls = snapshot_obj.get_disk_snapshots(pool_name, image_name)
        return snaps_ls

    def rollback_to_snapshot(self, pool_name, image_name, snap_name):
        check = False
        snapshot_obj = Snapshots()
        check = snapshot_obj.rollback_to_snapshot(pool_name, image_name, snap_name)
        return check

    def create_snapshot(self, pool_name, image_name, snap_name):
        created = False
        snapshot_obj = Snapshots()
        created = snapshot_obj.create_snapshot(pool_name, image_name, snap_name)
        return created

    def delete_snapshot(self, pool_name, image_name, snap_name):
        deleted = False
        snapshot_obj = Snapshots()
        deleted = snapshot_obj.delete_snapshot(pool_name, image_name, snap_name)
        return deleted

    def delete_snapshots(self, pool_name, image_name):
        deleted = False
        snapshot_obj = Snapshots()
        deleted = snapshot_obj.delete_snapshots(pool_name, image_name)
        return deleted

    def get_all_images(self, pool_name):
        snapshot_obj = Snapshots()
        images_ls = snapshot_obj.get_all_images(pool_name)
        return images_ls

    # ################################################################################################################ #
    #                                                    Replication                                                   #
    # ################################################################################################################ #

    def update_disk_metadata(self, updated_disk_meta):
        """
        :type updated_disk_meta: DiskMeta
        """

        cluster = self.connect()
        disk = DiskMeta()
        pool_name = updated_disk_meta.pool
        status = ManageDiskStatus.error
        attr_object =""

        if cluster != -1:
            try:
                io_ctx = cluster.open_ioctx(pool_name)
                disk_metas = self.get_disks_meta()
                disk_name_is_exists = False
                status = 0

                for i in disk_metas:
                    if i.disk_name == updated_disk_meta.disk_name:
                        disk_name_is_exists = True
                        break

                attr = self.read_image_metadata(self.conf_api.get_image_name_prefix() + updated_disk_meta.id, pool_name)
                petasan = attr.get(self.conf_api.get_image_meta_key())

                if petasan:
                    disk.load_json(petasan)

                if updated_disk_meta.disk_name is not None and updated_disk_meta.disk_name != disk.disk_name and disk_name_is_exists:
                    status = ManageDiskStatus.disk_name_exists

                if status != ManageDiskStatus.disk_name_exists:
                    attr_object = self.__get_header_object(self.conf_api.get_image_name_prefix() + updated_disk_meta.id,
                                                           pool_name)

                if not disk.id or len(disk.id) == 0:
                    # attach first time non-PetaSAN disk
                    disk.id = updated_disk_meta.id

                if updated_disk_meta.disk_name is not None:
                    disk.disk_name = updated_disk_meta.disk_name

                if updated_disk_meta.size is not None:
                    if updated_disk_meta.size > disk.size:
                        size = updated_disk_meta.size * 1024 ** 3
                        rbd.Image(io_ctx, str(self.conf_api.get_image_name_prefix() + updated_disk_meta.id)).resize(
                            size)
                        disk.size = updated_disk_meta.size

                    disk.create_date = updated_disk_meta.create_date
                    disk.acl = updated_disk_meta.acl
                    disk.user = updated_disk_meta.user
                    disk.password = updated_disk_meta.password
                    disk.iqn = updated_disk_meta.iqn
                    disk.pool = updated_disk_meta.pool
                    disk.paths = updated_disk_meta.paths
                    disk.wwn = updated_disk_meta.wwn
                    disk.data_pool = updated_disk_meta.data_pool
                    disk.description = updated_disk_meta.description
                    disk.is_replication_target = updated_disk_meta.is_replication_target
                    disk.replication_info = updated_disk_meta.replication_info

                    io_ctx.set_xattr(str(attr_object), str(self.conf_api.get_image_meta_key()), disk.write_json())
                    status = ManageDiskStatus.done

                io_ctx.close()

            except Exception as e:
                if status == -3:
                    logger.error("Error while updating image %s , disk name exists." % updated_disk_meta.disk_name)
                elif status == -1:
                    logger.error(
                        "Error while updating image %s, cannot connect to cluster." % updated_disk_meta.disk_name)
                elif status == 2:
                    logger.error("Error while updating image %s, could not add metadata." % updated_disk_meta.id)
                elif status == 1:
                    logger.warning("Error while updating image %s, connection not closed" % updated_disk_meta.id)

                logger.exception(e.message)

            cluster.shutdown()
            return True

        else:
            return -1


    def remove_disk_metadata(self, image_name, pool):
        """
        remove image metadata , given image name and pool name
        """
        cluster = self.connect()
        io_ctx = None
        if cluster != -1:
            try:
                io_ctx = cluster.open_ioctx(pool)
                attr = self.read_image_metadata(image_name, pool)
                petasan = attr.get(self.conf_api.get_image_meta_key())

                if petasan:
                    attr_object = self.__get_header_object(image_name, pool)
                    deleted = io_ctx.rm_xattr(str(attr_object), str(self.conf_api.get_image_meta_key()))

                    io_ctx.close()
                    cluster.shutdown()
                    if deleted:
                        return True

            except MetadataException as e:
                logger.exception("remove_disk_metadata >> " + str(e.message))
            except DiskListException as e:
                logger.exception("remove_disk_metadata >> " + str(e.message))
            except Exception as e:
                logger.exception("remove_disk_metadata >> " + str(e.message))

            io_ctx.close()
            cluster.shutdown()
            return False

        else:
            return -1


