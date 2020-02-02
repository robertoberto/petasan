#! /usr/bin/python
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

from PetaSAN.core.common.CustomException import DiskListException, CephException, MetadataException, PoolException
from PetaSAN.core.config.api import ConfigAPI

import argparse
import json
import sys
import os
import datetime
from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.backend.replication.replication_handler import ReplicationHandler
from PetaSAN.backend.manage_replication_jobs import ManageReplicationJobs
from PetaSAN.backend.replication.manage_disk_replication_info import ManageDiskReplicationInfo
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.ceph import ceph_disk as ceph_disk
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.enums import Status
from PetaSAN.core.consul.api import ConsulAPI


class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        subparser = parser.add_subparsers()

        subp_disks_meta = subparser.add_parser('disks-meta')
        subp_disks_meta.set_defaults(func = get_disks_meta_list)

        subp_disks_replicated_meta = subparser.add_parser('replicated-disks-meta')
        subp_disks_replicated_meta.set_defaults(func=get_replicated_disks_list)

        subp_disk_meta = subparser.add_parser('disk-meta')
        subp_disk_meta.set_defaults(func = get_diskmeta)
        subp_disk_meta.add_argument('--disk_id', help='disk id', required=True)

        subp_update_replication_info = subparser.add_parser('update-replication-info')
        subp_update_replication_info.set_defaults(func = update_replication_info)
        subp_update_replication_info.add_argument('--disk_id', help='disk id', required=True)
        subp_update_replication_info.add_argument('--src_disk_id', help='source disk id', required=True)
        subp_update_replication_info.add_argument('--src_disk_name', help='source disk name', required=True)
        subp_update_replication_info.add_argument('--src_cluster_name', help='source cluster name', required=True)
        subp_update_replication_info.add_argument('--src_cluster_fsid', help='source cluster fsid', required=True)
        subp_update_replication_info.add_argument('--dest_disk_id', help='destination disk id', required=True)
        subp_update_replication_info.add_argument('--dest_disk_name', help='destination disk name', required=True)
        subp_update_replication_info.add_argument('--dest_cluster_name', help='destination cluster name', required=True)
        subp_update_replication_info.add_argument('--dest_cluster_fsid', help='destination cluster fsid', required=True)
        subp_update_replication_info.add_argument('--dest_cluster_ip', help='destination cluster ip', required=True)

        subp_delete_replication_info = subparser.add_parser('delete-replication-info')
        subp_delete_replication_info.set_defaults(func = delete_replication_info)
        subp_delete_replication_info.add_argument('--disk_id', help='disk id', required=True)

        subp_get_disk_snapshots = subparser.add_parser('snapshot-list')
        subp_get_disk_snapshots.set_defaults(func = get_disk_snapshots)
        subp_get_disk_snapshots.add_argument('--disk_id', help='disk id', required=True)

        subp_delete_snapshot = subparser.add_parser('delete-snapshot')
        subp_delete_snapshot.set_defaults(func = delete_snapshot)
        subp_delete_snapshot.add_argument('--disk_id', help='disk id', required=True)
        subp_delete_snapshot.add_argument('--snapshot_name', help='snapshot name', required=True)

        subp_delete_snapshots = subparser.add_parser('delete-snapshots')
        subp_delete_snapshots.set_defaults(func = delete_snapshots)
        subp_delete_snapshots.add_argument('--disk_id', help='disk id', required=True)

        subp_rollback_snapshot = subparser.add_parser('rollback-snapshot')
        subp_rollback_snapshot.set_defaults(func = rollback_snapshot)
        subp_rollback_snapshot.add_argument('--disk_id', help='disk id', required=True)
        subp_rollback_snapshot.add_argument('--snapshot_name', help='snapshot name', required=True)

        subp_cluster_fsid = subparser.add_parser('cluster-fsid')
        subp_cluster_fsid.set_defaults(func = get_dest_cluster_fsid)

        subp_run_replication_job = subparser.add_parser('run-replication-job')
        subp_run_replication_job.set_defaults(func = run_replication_job)
        subp_run_replication_job.add_argument('--job_id', help='replication job_id', required=True)

        subp_stop_dest_disk = subparser.add_parser('stop-disk')
        subp_stop_dest_disk.set_defaults(func = stop_dest_disk)
        subp_stop_dest_disk.add_argument('--disk_id', help='disk id', required=True)

        subp_disks_meta = subparser.add_parser('replication-folder-check')
        subp_disks_meta.set_defaults(func = check_replication_folder)

        subp_images_names = subparser.add_parser('images_names')
        subp_images_names.set_defaults(func = get_all_images)
        subp_images_names.add_argument('--pool', help='pool name', required=True)

        subp_images_names = subparser.add_parser('dest-cluster-name')
        subp_images_names.set_defaults(func=get_dest_cluster_name)


        args = parser.parse_args()
        return args


def main_catch(func, args):
    try:
        func(args)

    except Exception as e:
        print ('Exception message :')
        print (str(e.message))


def main(argv):
    args = Prepare().parser()
    main_catch(args.func, args)

# ######################################################################################################################

def get_disks_meta_list(args):
    # Getting disk's metadata for "Remote Cluster" disks on all pools (DiskMeta Objects):
    try:
        disks_ls = []
        disks_metadata_ls = ManageDisk().get_disks_meta()
        for disk_meta_entity in disks_metadata_ls:
            entity_dict = disk_meta_entity.__dict__
            disks_ls.append(entity_dict)

        print(json.dumps(disks_ls, indent=4, sort_keys=False))
        sys.exit(0)

    except DiskListException as e:
        print("Error : DiskListException - {}".format(str(e.message)))
        sys.exit(-1)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : CephException - , {}".format(str(e.message)))
            sys.exit(-1)

    except MetadataException as e:
        print("Error : MetadataException - {}".format(str(e.message)))
        sys.exit(-1)

    except Exception as e:
        print("Error : Exception - {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################

def get_diskmeta(args):
    # Getting a specific disk metadata from "Remote Cluster" giving a disk_id (DiskMeta Objects):
    try:
        disk_id = args.disk_id
        ceph_api = CephAPI()
        disk_metadata = ceph_api.get_diskmeta(disk_id)
        diskmeta_dict = disk_metadata.__dict__
        print(json.dumps(diskmeta_dict, indent=4, sort_keys=False))
        sys.exit(0)

    except PoolException as e:
        if e.id == PoolException.CANNOT_GET_POOL:
            print("Error : PoolException - {}".format(str(e.message)))
            sys.exit(-1)

    except DiskListException as e:
        print("Error : DiskListException - {}".format(str(e.message)))
        sys.exit(-1)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : CephException - {}".format(str(e.message)))
            sys.exit(-1)

    except MetadataException as e:
        print("Error : MetadataException - {}".format(str(e.message)))
        sys.exit(-1)

    except Exception as e:
        print("Error : Exception - {}".format(str(e.message)))
        sys.exit(-1)


# ######################################################################################################################

def get_replicated_disks_list(args):
    # Getting disk's metadata for "Remote Cluster" replicated disks on all pools (DiskMeta Objects):
    try:
        disks_metadata_ls = ManageDisk().get_disks_meta()
        disks = []
        for disk_meta_entity in disks_metadata_ls:
            if disk_meta_entity.is_replication_target:
                disks.append(disk_meta_entity.__dict__)
        print(json.dumps(disks, indent=4, sort_keys=False))
        sys.exit(0)

    except DiskListException as e:
        print("Error : DiskListException - {}".format(str(e.message)))
        sys.exit(-1)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : CephException - {}".format(str(e.message)))
            sys.exit(-1)

    except MetadataException as e:
        print("Error : MetadataException - {}".format(str(e.message)))
        sys.exit(-1)

    except Exception as e:
        print("Error : Exception - {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################

def update_replication_info(args):
    disk_id = args.disk_id
    try:
        src_disk_id = args.src_disk_id
        src_disk_name = args.src_disk_name
        src_cluster_name = args.src_cluster_name
        src_cluster_fsid = args.src_cluster_fsid
        dest_disk_id = args.dest_disk_id
        dest_disk_name = args.dest_disk_name
        dest_cluster_name = args.dest_cluster_name
        dest_cluster_ip = args.dest_cluster_ip
        dest_cluster_fsid = args.dest_cluster_fsid

        new_replication_info = {
            'src_disk_id': src_disk_id,
            'src_disk_name': src_disk_name,
            'src_cluster_fsid': src_cluster_fsid,
            'src_cluster_name': src_cluster_name,
            'dest_disk_id': dest_disk_id,
            'dest_disk_name': dest_disk_name,
            'dest_cluster_name': dest_cluster_name,
            'dest_cluster_ip': dest_cluster_ip,
            'dest_cluster_fsid': dest_cluster_fsid
        }

        ceph_api = CephAPI()
        disks_metadata = ceph_api.get_diskmeta(disk_id)

        mng_rep_info = ManageDiskReplicationInfo()
        confirm = mng_rep_info.update_replication_info(disks_metadata, new_replication_info)

        if not confirm:
            print("Error : Cannot update replication info on destination disk " + disk_id)
            sys.exit(-1)

        sys.exit(0)

    except PoolException as e:
        if e.id == PoolException.CANNOT_GET_POOL:
            print("Error : Cannot update replication info on destination disk " + disk_id + " , {}".format(str(e.message)))
            sys.exit(-1)

    except DiskListException as e:
        print("Error : Cannot update replication info on destination disk " + disk_id + " , {}".format(str(e.message)))
        sys.exit(-1)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : Cannot update replication info on destination disk " + disk_id + " , {}".format(str(e.message)))
            sys.exit(-1)

    except MetadataException as e:
        print("Error : Cannot update replication info on destination disk " + disk_id + " , {}".format(str(e.message)))
        sys.exit(-1)

    except Exception as e:
        print("Error : Cannot update replication info on destination disk " + disk_id + " , {}".format(str(e.message)))
        sys.exit(-1)


# ######################################################################################################################

def delete_replication_info(args):
    disk_id = args.disk_id
    try:
        ceph_api = CephAPI()
        disks_metadata = ceph_api.get_diskmeta(disk_id)

        mng_rep_info = ManageDiskReplicationInfo()
        confirm = mng_rep_info.delete_replication_info(disks_metadata)

        if not confirm:
            print("Error : Cannot delete replication info on destination disk " + disk_id)
            sys.exit(-1)

        sys.exit(0)

    except PoolException as e:
        if e.id == PoolException.CANNOT_GET_POOL:
            print("Error : Cannot delete replication info on destination disk " + disk_id + " , {}".format(str(e.message)))
            sys.exit(-1)

    except DiskListException as e:
        print("Error : Cannot delete replication info on destination disk " + disk_id + " , {}".format(str(e.message)))
        sys.exit(-1)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : Cannot delete replication info on destination disk " + disk_id + " , {}".format(str(e.message)))
            sys.exit(-1)

    except MetadataException as e:
        print("Error : Cannot delete replication info on destination disk " + disk_id + " , {}".format(str(e.message)))
        sys.exit(-1)

    except Exception as e:
        print("Error : Cannot delete replication info on destination disk " + disk_id + " , {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################

def get_disk_snapshots(args):
    disk_id = args.disk_id
    try:
        ceph_api = CephAPI()
        image_name = "image-" + disk_id
        pool_name = ceph_api.get_pool_bydisk(disk_id)

        # If pool inactive #
        if pool_name is None:
            print("Error : Cannot get pool of disk {}".format(str(disk_id)))
            sys.exit(-1)

        else:
            snaps_ls = ceph_api.get_disk_snapshots(pool_name, image_name)
            print(json.dumps(snaps_ls))
            sys.exit(0)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : CephException - {} , Cannot get disk {} snapshots.".format(str(e.message), disk_id))
            sys.exit(-1)

    except Exception as e:
        print("Error : Exception - {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################

def delete_snapshot(args):
    disk_id = args.disk_id
    snap_name = args.snapshot_name
    try:
        ceph_api = CephAPI()
        image_name = str(ceph_api.conf_api.get_image_name_prefix() + disk_id)
        pool_name = ceph_api.get_pool_bydisk(disk_id)                                       # getting pool_name from disk_id

        # If pool inactive #
        if pool_name is None:
            print("Error : Cannot get pool of disk {}".format(str(disk_id)))
            sys.exit(-1)

        else:
            confirm = ceph_api.delete_snapshot(pool_name, image_name, snap_name)

            if not confirm:
                print("Error : Cannot delete snapshot \"" + snap_name + "\" of disk " + disk_id)
                sys.exit(-1)

        sys.exit(0)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : CephException - " + str(e.message) + " , Cannot delete snapshot \"" + snap_name + "\" of disk " + disk_id)
            sys.exit(-1)

    except Exception as e:
        print("Error : Exception - {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################

def rollback_snapshot(args):
    disk_id = args.disk_id
    snap_name = args.snapshot_name
    try:
        ceph_api = CephAPI()
        image_name = str(ceph_api.conf_api.get_image_name_prefix() + disk_id)
        pool_name = ceph_api.get_pool_bydisk(disk_id)                                       # getting pool_name from disk_id

        # If pool inactive #
        if pool_name is None:
            print("Error : Cannot get pool of disk {}".format(str(disk_id)))
            sys.exit(-1)

        else:
            confirm = ceph_api.rollback_to_snapshot(pool_name, image_name, snap_name)

            if not confirm:
                print("Error : Cannot rollback disk " + disk_id + " to snapshot " + snap_name)
                sys.exit(-1)

        sys.exit(0)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : CephException - " + str(e.message) + " , Cannot rollback disk " + disk_id + " to snapshot " + snap_name)
            sys.exit(-1)

    except Exception as e:
        print("Error : Exception - {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################

def delete_snapshots(args):
    disk_id = args.disk_id
    try:
        ceph_api = CephAPI()
        image_name = str(ceph_api.conf_api.get_image_name_prefix() + disk_id)
        pool_name = ceph_api.get_pool_bydisk(disk_id)                                       # getting pool_name from disk_id

        # If pool inactive #
        if pool_name is None:
            print("Error : Cannot get pool of disk {}".format(str(disk_id)))
            sys.exit(-1)

        else:
            confirm = ceph_api.delete_snapshots(pool_name, image_name)

            if not confirm:
                print("Error : Cannot delete all snapshots of disk " + disk_id)
                sys.exit(-1)

        sys.exit(0)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : CephException - " + str(e.message) + " , Cannot delete all snapshots of disk " + disk_id)
            sys.exit(-1)

    except Exception as e:
        print("Error : Exception - {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################

def get_dest_cluster_fsid(args):
    try:
        destination_fsid = ceph_disk.get_fsid(configuration().get_cluster_name())
        print(json.dumps(destination_fsid))
        sys.exit(0)

    except Exception as e:
        print("Error : {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################

def run_replication_job(args):
    job_id = args.job_id
    replication_handler = ReplicationHandler()
    try:
        replication_handler.run_replication_job(job_id)
        sys.exit(0)

    except Exception as e:
        manage_replication_jobs = ManageReplicationJobs()
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} | Error : {}.".format(system_date_time, str(job_id), str(e.message))
        manage_replication_jobs.log_replication_job(job_id, text)
        sys.exit(-1)

# ######################################################################################################################

def stop_dest_disk(args):
    disk_id = args.disk_id
    consul_api = ConsulAPI()
    try:
        kv = consul_api.find_disk(disk_id)
        if kv is not None:
            manage_disk = ManageDisk()
            status = manage_disk.stop(disk_id)

            if status != Status.done:
                print('Error : Cannot stop disk , id = ' + disk_id)
                sys.exit(-1)

            sys.exit(0)

        else:
            print('Disk {} is already stopped.'.format(disk_id))
            sys.exit(0)

    except Exception as e:
        print("Error : Exception - {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################

def check_replication_folder(args):
    # home = expanduser('~')
    try:
        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        sys.exit(0)

    except Exception as e:
        print("Error : {}".format(str(e.message)))
        sys.exit(-1)


# ######################################################################################################################

def get_all_images(args):
    try:
        ceph_api = CephAPI()
        pool_name = args.pool
        images_ls = ceph_api.get_all_images(pool_name)
        print(json.dumps(images_ls))
        sys.exit(0)

    except CephException as e:
        if e.id == CephException.GENERAL_EXCEPTION:
            print("Error : {} , Cannot get images list.".format(str(e.message)))
            sys.exit(-1)

    except Exception as e:
        print("Error : Exception , {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################

def get_dest_cluster_name(args):
    try:
        cluster_name = configuration().get_cluster_name(custom_name=True)
        print(json.dumps(cluster_name))
        sys.exit(0)

    except Exception as e:
        print("Error : {}".format(str(e.message)))
        sys.exit(-1)


if __name__ == '__main__':
   main(sys.argv[1:])

