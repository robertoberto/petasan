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
import random
import time
from PetaSAN.backend.manage_pools import ManagePools
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.cluster.job_manager import JobManager
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.ceph.ceph_authenticator import CephAuthenticator
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.cmd import call_cmd
from PetaSAN.core.common.log import logger
from PetaSAN.core.common.enums import Status
from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.job import JobType
from PetaSAN.core.common.CustomException import DiskListException, CephException, MetadataException, PoolException


def clear_disk(args):
    disk_id = args.disk_id
    image_name = "image-" + disk_id

    try:
        # Get which ceph user is using this function & get his keyring file path #
        # ---------------------------------------------------------------------- #
        ceph_auth = CephAuthenticator()

        config = configuration()
        cluster_name = config.get_cluster_name()

        # Get disk metadata :
        # -------------------
        ceph_api = CephAPI()
        disk_metadata = ceph_api.get_diskmeta(disk_id)

        # Get pool name :
        # ---------------
        pool_name = disk_metadata.pool
        data_pool = ""

        # Check if disk has been created on replicated pool or erasure pool :
        # -------------------------------------------------------------------
        if len(disk_metadata.data_pool) > 0 :
            data_pool = disk_metadata.data_pool

        tmp_image_name = "tmp_disk_" + disk_metadata.id

        # (1.) Check if a previous tmp image for this disk is still existed :
        # ===================================================================
        images_list = ceph_api.get_all_images(pool_name)

        for image in images_list:
            if tmp_image_name in image:
                # Delete image #
                cmd = "rbd rm {}/{} {} --cluster {}".format(pool_name, image, ceph_auth.get_authentication_string(), cluster_name)
                if not call_cmd(cmd):
                    print("Error : clear_disk.py script : cannot remove tmp image ,\ncmd : " + cmd)
                    sys.exit(-1)

        print("Stage 1 :\n\tCheck if a previous tmp image for this disk is still existed > (Completed)")
        logger.info("Stage 1 :\n\tCheck if a previous tmp image for this disk is still existed > (Completed)")

        # (2.) Stop old disk :
        # ====================
        consul_api = ConsulAPI()
        kv = consul_api.find_disk(disk_id)
        if kv is not None:
            manage_disk = ManageDisk()
            status = manage_disk.stop(disk_id)

            if status != Status.done:
                print('Error : Cannot stop disk , id = ' + disk_id)
                sys.exit(-1)

            print("Stage 2 :\n\tStop old disk > (Completed)")
            logger.info("Stage 2 :\n\tStop old disk > (Completed)")
            time.sleep(3)

            # (3.) Check if old disk is stopped or not :
            # ==========================================
            if len(data_pool) > 0 :
                pool_type = "erasure"
                _confirm_disk_stopped(data_pool, disk_id, pool_type)
            else:
                pool_type = "replicated"
                _confirm_disk_stopped(pool_name, disk_id, pool_type)


            print("Stage 3 :\n\tConfirm that disk is completely stopped > (Completed)")
            logger.info("Stage 3 :\n\tConfirm that disk is completely stopped > (Completed)")


        else:
            print("Stage 2 :\n\tStop old disk > (Completed)")
            logger.info("Stage 2 :\n\tStop old disk > (Completed)")

            print("Stage 3 :\n\tConfirm that disk is completely stopped > (Completed)")
            logger.info("Stage 3 :\n\tConfirm that disk is completely stopped > (Completed)")
            print('\tclear_disk.py script : disk {} is already stopped'.format(disk_id))


        # (4.) Create a tmp image (not PetaSAN image) :
        # =============================================
        # Generate a random value between 1 and 99999 #
        random_no = str(random.randint(1,100000))
        tmp_image_name = tmp_image_name + "_" + str(random_no)
        image_size = disk_metadata.size * 1024

        if len(data_pool) > 0 :
            cmd = "rbd create {}/{} --size {} --data-pool {} {} --cluster {}".format(pool_name, tmp_image_name, image_size, data_pool, ceph_auth.get_authentication_string(), cluster_name)
        else:
            cmd = "rbd create {}/{} --size {} {} --cluster {}".format(pool_name, tmp_image_name, image_size, ceph_auth.get_authentication_string(), cluster_name)

        if not call_cmd(cmd):
            print("Error : clear_disk.py script : cannot create new tmp image ,\ncmd : " + cmd)
            sys.exit(-1)

        print("Stage 4 :\n\tCreate a tmp image called ( " + tmp_image_name + " ) > (Completed)")
        logger.info("Stage 4 :\n\tCreate a tmp image called ( " + tmp_image_name + " ) > (Completed)")

        # (5.) Run script to copy "old disk" metadata to new "tmp_disk" :
        # ===============================================================
        metadata_script_file = ConfigAPI().get_disk_meta_script_path()

        # Function : read_disks_metadata :
        parser_key_1 = "read"
        arg_1 = "--image"
        arg_2 = "--pool"

        # Function : set_disk_metadata :
        parser_key_2 = "write"
        arg_3 = "--file"

        cmd = metadata_script_file + " " + parser_key_1 + " " + arg_1 + " " + image_name + " " + arg_2 + " " + pool_name +\
              " | " + metadata_script_file + " " + parser_key_2 + " " + arg_1 + " " + tmp_image_name + " " + arg_2 + " " + pool_name

        if not call_cmd(cmd):
            print("Error : clear_disk.py script : cannot copy metadata from old disk to new tmp image ,\ncmd : " + cmd)
            sys.exit(-1)

        print("Stage 5 :\n\tRun script to copy 'old disk' metadata to new 'tmp_disk' > (Completed)")
        logger.info("Stage 5 :\n\tRun script to copy 'old disk' metadata to new 'tmp_disk' > (Completed)")

        time.sleep(3)

        # (6.) Remove metadata of old disk :
        # ===========================================================
        old_image_name = str(ceph_api.conf_api.get_image_name_prefix() + disk_metadata.id)
        confirm = ceph_api.remove_disk_metadata(old_image_name, disk_metadata.pool)

        if not confirm:
            print("Error : clear_disk.py script : cannot remove metadata of old disk")
            # sys.exit(-1)

        print("Stage 6 :\n\tRemove metadata of old disk > (Completed)")
        logger.info("Stage 6 :\n\tRemove metadata of old disk > (Completed)")

        # (7.) Rename old disk image name with "deleted-" + disk_id + random_no:
        # ======================================================================
        new_image_name = "deleted-" + disk_metadata.id + "-" + random_no
        cmd = "rbd mv {}/{} {} {} --cluster {}".format(pool_name, image_name, new_image_name, ceph_auth.get_authentication_string(), cluster_name)
        if not call_cmd(cmd):
            print("Error : clear_disk.py script : cannot rename old image from {} to {} ,\ncmd : {}".format(image_name, new_image_name,
                                                                                                cmd))
            sys.exit(-1)

        print("Stage 7 :\n\tRename old disk image name with ( " + new_image_name + " ) > (Completed)")
        logger.info("Stage 7 :\n\tRename old disk image name with ( " + new_image_name + " ) > (Completed)")

        time.sleep(5)

        # (8.) Rename "tmp_disk" with old disk image name :
        # =================================================
        cmd = "rbd mv {}/{} {} {} --cluster {}".format(pool_name, tmp_image_name, image_name, ceph_auth.get_authentication_string(), cluster_name)
        if not call_cmd(cmd):
            print("Error : clear_disk.py script : cannot rename \"tmp_disk\" from {} to {} ,\ncmd : {}".format(tmp_image_name, image_name,
                                                                                                cmd))
            sys.exit(-1)

        print("Stage 8 :\n\tRename 'tmp_disk' with old disk image name > (Completed)")
        logger.info("Stage 8 :\n\tRename 'tmp_disk' with old disk image name > (Completed)")

        time.sleep(5)

        jm = JobManager()
        id = jm.add_job(JobType.DELETE_DISK, new_image_name + ' ' + pool_name)

        print("Stage 9 :\n\tStart a job to remove old disk image , job id = " + str(id))
        logger.info("Stage 9 :\n\tStart a job to remove old disk image , job id = " + str(id))

        sys.exit(0)

    except PoolException as e:
        print("Error : PoolException , {}".format(e.message))
        logger.error("Clear Disk Error : PoolException , {}".format(e.message))
        sys.exit(-1)

    except DiskListException as e:
        print("Error : DiskListException , {}".format(e.message))
        logger.error("Clear Disk Error : DiskListException , {}".format(e.message))
        sys.exit(-1)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : CephException , {}".format(e.message))
        logger.error("Clear Disk Error : CephException , {}".format(e.message))
        sys.exit(-1)

    except MetadataException as e:
        print("Error : MetadataException , {}".format(e.message))
        logger.error("Clear Disk Error : MetadataException , {}".format(e.message))
        sys.exit(-1)

    except Exception as e:
        print("Error : Exception , {}".format(e.message))
        logger.error("Clear Disk Error : Exception , {}".format(e.message))
        sys.exit(-1)

########################################################################################################################

def _confirm_disk_stopped(pool, disk_id, pool_type, wait_interval=10, wait_count=10):
    running_pool_disks = _get_running_pool_disks(pool, pool_type)
    print("\trunning_pool_disks" + " --> " + str(running_pool_disks))
    logger.info("\trunning_pool_disks" + " --> " + str(running_pool_disks))

    if len(running_pool_disks) == 0 :
        return

    while 0 < wait_count:
        time.sleep(wait_interval)
        running_pool_disks = _get_running_pool_disks(pool, pool_type)

        if not (disk_id in running_pool_disks):
            return
        wait_count -= 1

########################################################################################################################

def _get_running_pool_disks(pool, pool_type):
    consul = ConsulAPI()
    running_pool_disks = []
    meta_disk = ManageDisk().get_disks_meta()

    pool_disks = set()

    if pool_type == "replicated":
        if len(meta_disk) > 0:
            for meta in meta_disk:
                if meta.pool == pool:
                   pool_disks.add(meta.id)

    elif pool_type == "erasure":
        if len(meta_disk) > 0:
            for meta in meta_disk:
                if meta.data_pool == pool:
                    pool_disks.add(meta.id)


    running_disks = consul.get_running_disks()
    for running_disk in running_disks :
        if running_disk in pool_disks :
            running_pool_disks.append(running_disk)

    return running_pool_disks

########################################################################################################################

def main():
    parser = argparse.ArgumentParser(description="This is a script that will clear destination disk.")
    parser.add_argument("--disk_id",
                        help="id of the disk",
                        required=True)

    parser.set_defaults(func=clear_disk)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
    sys.exit(0)

