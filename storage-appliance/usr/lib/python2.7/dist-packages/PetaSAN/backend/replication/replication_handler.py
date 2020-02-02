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

import os
import re
import subprocess
import time
import datetime
from time import sleep
import psutil
from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.backend.manage_replication_jobs import ManageReplicationJobs
from PetaSAN.backend.replication.manage_tmp_files import ManageTmpFile
from PetaSAN.backend.replication.progress_updater import ProgressUpdaterThread
from PetaSAN.backend.replication.command_builder import CommandBuilder
from PetaSAN.backend.replication.manage_destination_cluster import ManageDestinationCluster
from PetaSAN.backend.replication.manage_remote_replication import ManageRemoteReplication
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.entity.disk_info import DiskMeta
from PetaSAN.core.entity.models.replication_active_job import ReplicationActiveJob
from PetaSAN.core.common.log import logger
from PetaSAN.core.common.CustomException import ConsulException, ReplicationException, DiskListException, PoolException, \
    MetadataException, CephException


class ReplicationHandler:
    def __init__(self):
        self.heartbeat_failure = 300
        self.snapshot_list = []

    def run_replication_job(self, job_id):
        mng_rep = ManageReplicationJobs()

        try:
            # FIRST : get current replication job info from consul as job_entity :
            job_entity = mng_rep.get_replication_job(job_id)

            if job_entity is None:
                # if job entity is deleted #
                logger.error("Error in running replication job. Can not find replication job {}".format(job_id))
                return False

            text = "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            mng_rep.log_replication_job(job_id, text)

            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Run replication job ...".format(system_date_time, job_id)
            mng_rep.log_replication_job(job_id, text)

            # SECOND : create new instance (active_job) with that job_id , start_time :
            time_stamp = str(int(round(time.time())))

            active_job = ReplicationActiveJob()
            active_job.job_id = job_id + "-" + time_stamp
            active_job.job_name = job_entity.job_name
            active_job.start_time = str(datetime.datetime.now()).split('.')[0]

            # THIRD : get pid of process :
            pid = str(os.getpid())
            active_job.pid = pid

            # FOURTH : define variable (prv_job_id) , and check if a previous job is running :
            prv_job_id = job_id
            prv_active_job_entity = self.get_active_job(prv_job_id)

            # If previous job instance is active :
            ######################################
            if prv_active_job_entity:
                # -- add log -- #
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Previous job instance ({}) is still running".format(
                    system_date_time, str(job_id), str(prv_active_job_entity.start_time))
                mng_rep.log_replication_job(job_id, text)

                # check if previous job is healthy or not :
                healthy = self.is_job_healthy(prv_active_job_entity)

                if healthy is None:
                    pass

                elif not healthy:
                    # -- add log -- #
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Previous job instance ({}) is not healthy.".format(
                        system_date_time, str(job_id), str(prv_active_job_entity.start_time))
                    mng_rep.log_replication_job(job_id, text)

                    # cancel previous job :
                    result = self.cancel_active_job(prv_active_job_entity.job_id)

                    if not result:
                        system_date_time = str(datetime.datetime.now()).split('.')[0]
                        text = "{} - Job {} | Previous job instance ({}) could not be canceled.".format(
                            system_date_time, str(job_id), str(prv_active_job_entity.start_time))
                        mng_rep.log_replication_job(job_id, text)
                        return False

                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Previous job instance ({}) has been canceled.".format(
                        system_date_time, str(job_id), str(prv_active_job_entity.start_time))
                    mng_rep.log_replication_job(job_id, text)

                else:
                    # adding a log in Consul :
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Previous job instance ({}) is still running , so the new job instance ({}) not started.".format(
                        system_date_time, str(job_id), str(prv_active_job_entity.start_time), str(active_job.start_time))
                    mng_rep.log_replication_job(job_id, text)

                    return False

            # Start the New Job Instance : ( If previous job instance is inactive or we have canceled a previous job )
            ##############################
            start_rep = self.start_replication(active_job, job_entity, job_id)

            if not start_rep:
                return False

            return True

        except ReplicationException as e:
            if e.id == ReplicationException.CONNECTION_TIMEOUT:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Connection Timed Out , {}".format(system_date_time, str(job_id), str(e.message))
                mng_rep.log_replication_job(job_id, text)

            elif e.id == ReplicationException.CONNECTION_REFUSED:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Connection Refused , {}".format(system_date_time, str(job_id), str(e.message))
                mng_rep.log_replication_job(job_id, text)

            elif e.id == ReplicationException.PERMISSION_DENIED:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Permission Denied , {}".format(system_date_time, str(job_id), str(e.message))
                mng_rep.log_replication_job(job_id, text)

            elif e.id == ReplicationException.GENERAL_EXCEPTION:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Replication General Exception , {}".format(system_date_time, str(job_id), str(e.message))
                mng_rep.log_replication_job(job_id, text)

            return False

        except ConsulException as e:
            if e.id == ConsulException.CONNECTION_TIMEOUT:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Consul Connection Timed Out , {}".format(system_date_time, str(job_id), str(e.message))
                mng_rep.log_replication_job(job_id, text)

            elif e.id == ConsulException.GENERAL_EXCEPTION:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Consul General Exception , {}".format(system_date_time, str(job_id), str(e.message))
                mng_rep.log_replication_job(job_id, text)

            return False

        except PoolException as e:
            if e.id == PoolException.CANNOT_GET_POOL:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | {}".format(system_date_time, str(job_id), str(e.message))
                mng_rep.log_replication_job(job_id, text)

            return False

        except DiskListException as e:
            if e.id == DiskListException.DISK_NOT_FOUND:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | {}".format(system_date_time, str(job_id), str(e.message))
                mng_rep.log_replication_job(job_id, text)

            return False

        except CephException as e:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | {}".format(system_date_time, str(job_id), str(e.message))
            mng_rep.log_replication_job(job_id, text)

        except MetadataException as e:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | {}".format(system_date_time, str(job_id), str(e.message))
            mng_rep.log_replication_job(job_id, text)

            return False

        except Exception as e:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | {}".format(system_date_time, str(job_id), str(e.message))
            mng_rep.log_replication_job(job_id, text)

            return False



    def start_replication(self, active_job, job_entity, job_id):
        if job_entity is None:
            # if job entity is deleted #
            logger.error("Error in starting replication job. Can not find replication job.")
            return False

        mng_remote_rep = ManageRemoteReplication()
        mng_remote_rep.cluster_name = job_entity.destination_cluster_name

        mng_rep = ManageReplicationJobs()

        consul_api = ConsulAPI()

        # Getting Destination Cluster info #
        # -------------------------------- #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(job_entity.destination_cluster_name)
        decrypted_key = dest_cluster.ssh_private_key
        dest_user_name = dest_cluster.user_name
        dest_cluster_ip = dest_cluster.remote_ip

        # -- add log -- #
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} | Stopping destination disk.".format(
            system_date_time, str(job_id))
        mng_rep.log_replication_job(job_id, text)

        # FIRST : Stop Destination Disk #
        # ----------------------------- #
        # Save private key in text file #
        mng_file = ManageTmpFile()

        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path()
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # Run script remotely at destination cluster #
        script_file = ConfigAPI().get_replication_script_path()
        parser_key = "stop-disk"

        arg1 = "--disk_id"

        # Define cmd command #
        cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} {} {}"'.format(sshkey_path, dest_user_name,
                                                                                       dest_cluster_ip, script_file,
                                                                                       parser_key , arg1,
                                                                                       job_entity.destination_disk_id)
        ret, stdout, stderr = exec_command_ex(cmd)

        # Delete 'sshkey_path' file #
        mng_file.delete_tmp_file(sshkey_path)

        if ret != 0:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = '{} - Job {} | Cannot stop destination disk {}'.format(system_date_time, str(job_entity.job_id), job_entity.destination_disk_id)

            if stderr and ('Connection refused' in stderr):
                text = '{} - Job {} | Cannot stop destination disk | Connection refused , Error = {}'.format(system_date_time, str(job_entity.job_id), stderr)

            elif stderr and ('Permission denied' in stderr):
                text = '{} - Job {} | Cannot stop destination disk | Permission denied , Error = {}'.format(system_date_time, str(job_entity.job_id), stderr)

            elif stderr and ("warning" not in stderr.lower()):
                text = '{} - Job {} | Cannot stop destination disk , Error = {}'.format(system_date_time, str(job_entity.job_id), stderr)

            else:
                text = '{} - Job {} | Cannot stop destination disk , Error = {}'.format(system_date_time, str(job_entity.job_id), stderr)

            mng_rep.log_replication_job(job_entity.job_id, text)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(
                system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)

            return False

        if stderr and ("warning" not in stderr.lower()):
            text = '{} - Job {} | Cannot stop destination disk , Error = {}'.format(system_date_time, str(job_entity.job_id), stderr)
            mng_rep.log_replication_job(job_entity.job_id, text)

        if stdout and ('Error' in stdout):
            text = '{} - Job {} | Cannot stop destination disk , Error = {}'.format(system_date_time, str(job_entity.job_id), stdout)
            mng_rep.log_replication_job(job_entity.job_id, text)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(
                system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)
            return False

        # Getting src disk id and dest disk id #
        src_disk_id = job_entity.source_disk_id
        dest_disk_id = job_entity.destination_disk_id

        # Setting data of remote cluster #
        mng_remote_rep.cluster_name = job_entity.destination_cluster_name
        mng_remote_rep.disk_id = job_entity.destination_disk_id  # dest_disk_id

        # SECOND : Getting metadata of source & destination disk #
        # ------------------------------------------------------ #
        # -- add log -- #
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} | Getting metadata of destination disk.".format(system_date_time, str(job_id))
        mng_rep.log_replication_job(job_id, text)

        # (1) get destination disk info :
        dest_disk_meta = mng_remote_rep.get_disk_meta()
        dest_disk_meta_obj = DiskMeta(dest_disk_meta)

        # -- add log -- #
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} | Getting metadata of source disk.".format(system_date_time, str(job_id))
        mng_rep.log_replication_job(job_id, text)

        # (2) get source disk info:
        src_disk_meta = mng_rep.get_src_disk_meta(src_disk_id)

        # (3) check if src_disk_meta exists :
        if src_disk_meta is None:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Failed to get source disk metadata.".format(system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)

            return False

        # (4) check if dest_disk_meta_obj exists :
        if dest_disk_meta_obj is None:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Failed to get destination disk metadata.".format(system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)

            return False

        # (5) check on --> source_cluster_fsid :
        if job_entity.source_cluster_fsid != src_disk_meta.replication_info['src_cluster_fsid']:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | source_cluster_fsid in job not matching source_cluster_fsid in source disk metadata.".format(
                system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)
            return False

        # (6) check on --> dest_cluster_fsid :
        if dest_cluster.cluster_fsid != dest_disk_meta_obj.replication_info['dest_cluster_fsid']:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | dest_cluster_fsid not matching dest_cluster_fsid in destination disk metadata.".format(
                system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed".format(system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)
            return False

        # (7) check on the size of both disks :
        if src_disk_meta.size != dest_disk_meta_obj.size:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Source disk size and destination disk size are different.".format(
                system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)
            return False

        # (8) check if dest disk is replicated enabled :
        if not dest_disk_meta_obj.is_replication_target:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Destination disk is not replication enabled.".format(system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)
            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(
                system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)
            return False

        # THIRD : Getting snapshots of source & destination disk #
        # ------------------------------------------------------ #
        # -- add log -- #
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} | Getting destination disk snapshots list.".format(system_date_time, str(job_id))
        mng_rep.log_replication_job(job_id, text)

        dest_snap_list = mng_remote_rep.get_dest_snapshots()

        # -- add log -- #
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} | Getting source disk snapshots list.".format(system_date_time, str(job_id))
        mng_rep.log_replication_job(job_id, text)

        src_snap_list = self.get_src_snapshots(src_disk_meta.pool, src_disk_meta.id)

        # -- CHECK IF -- #
        # (9) Only one snapshot found on both src and dest disks and the names of both snapshots are equal :
        if len(src_snap_list) == len(dest_snap_list) == 1 and src_snap_list[0] == dest_snap_list[0]:
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Matched source and destination disks snapshots.".format(
                system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)

            # rollback the dest disk to this snapshot :
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Rolling back destination disk to existed snapshot.".format(
                system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)

            mng_remote_rep.snapshot_name = dest_snap_list[0]
            mng_remote_rep.rollback_dest_snapshot()

        # -- OR CHECK IF -- #
        # (10) Mismatch snapshots , src or dest snapshots list is greater than one ,
        #      or one snapshot found but src snapshot name not match dest snapshot name  -->  Delete all snapshots
        if len(src_snap_list) != len(dest_snap_list) or \
                        len(src_snap_list) > 1 or \
                        len(dest_snap_list) > 1 or \
                (len(src_snap_list) == len(dest_snap_list) == 1 and src_snap_list[0] != dest_snap_list[0]):
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Mismatched source and destination disks snapshots.".format(system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)

            # delete snapshot from destination disk:
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Deleting destination disk snapshots.".format(system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)

            mng_remote_rep.delete_dest_snapshots()

            # delete snapshots from source disk :
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Deleting source disk snapshots.".format(system_date_time, str(job_id))
            mng_rep.log_replication_job(job_id, text)

            mng_rep.delete_snapshots(src_disk_meta.pool, src_disk_meta.id)

            src_snap_list = []
            dest_snap_list = []

        # FOURTH : call : do_run(job_entity)  #
        # ----------------------------------- #
        do_run = self.do_run(job_entity, active_job)

        if not do_run:
            return False

        return True


    def do_run(self, job_entity, active_job):
        if job_entity is None:
            # if job entity is deleted #
            logger.error("Error in running replication job. Can not find replication job.")
            return False

        mng_rep = ManageReplicationJobs()

        # FIRST : Save "active_job" in Consul #
        # ----------------------------------- #
        consul_api = ConsulAPI()
        consul_api.update_replication_active_job(active_job)
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} | Job instance ({}) | Started.".format(system_date_time,
                                                                          str(job_entity.job_id),
                                                                          str(active_job.start_time))
        mng_rep.log_replication_job(job_entity.job_id, text)

        # Setting data of remote cluster :
        mng_remote_rep = ManageRemoteReplication()
        mng_remote_rep.cluster_name = job_entity.destination_cluster_name
        mng_remote_rep.disk_id = job_entity.destination_disk_id

        # SECOND : Check if src_snapshot_list is empty , if so clear the destination disk #
        # ------------------------------------------------------------------------------- #
        ceph_api = CephAPI()
        src_disk_id = job_entity.source_disk_id
        src_disk_pool = ceph_api.get_pool_bydisk(src_disk_id)

        # If pool inactive #
        if src_disk_pool is None:
            raise PoolException(PoolException.CANNOT_GET_POOL, "Cannot get pool of disk " + str(src_disk_id))

        src_snapshot_list = self.get_src_snapshots(src_disk_pool, src_disk_id)

        # Clear destination disk if snapshot list is empty :
        if len(src_snapshot_list) == 0:
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job instance ({}) | Source disk has no snapshots , start clearing destination disk.".format(
                system_date_time, str(job_entity.job_id), str(active_job.start_time))
            mng_rep.log_replication_job(job_entity.job_id, text)

            try:
                mng_remote_rep.clear_disk()
            except Exception as e:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Job instance ({}) | {}.".format(
                    system_date_time, str(job_entity.job_id), str(active_job.start_time), str(e.message))
                mng_rep.log_replication_job(job_entity.job_id, text)

                # Delete Active Job Instance from Consul #
                # -------------------------------------- #
                consul_api = ConsulAPI()
                consul_api.delete_active_job(job_entity.job_id)

                # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
                # ------------------------------------------------------------------------ #
                result = consul_api.add_replication_failed_job(job_entity)

                # -- add log -- #
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Job Failed.".format(
                    system_date_time, str(job_entity.job_id))
                mng_rep.log_replication_job(job_entity.job_id, text)

                return False

        # THIRD : Before create new snapshot , execute --> pre_snap_url #
        # ------------------------------------------------------------- #
        if job_entity.pre_snap_url:
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job instance ({}) | Calling Pre Snapshot Script URL.".format(
                system_date_time, str(job_entity.job_id), str(active_job.start_time))
            mng_rep.log_replication_job(job_entity.job_id, text)

            exe_pre_url = self.execute_user_script(job_entity.pre_snap_url)

            if not exe_pre_url:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Job instance ({}) | Couldn't execute Pre Snapshot Script URL : {}.".format(
                    system_date_time, str(job_entity.job_id), str(active_job.start_time), job_entity.pre_snap_url)
                mng_rep.log_replication_job(job_entity.job_id, text)

        # FOURTH : Create new snapshot at source disk #
        # ------------------------------------------- #
        # Define a name for the new snapshot :
        serial = self.get_next_snap_serial(src_snapshot_list)
        snapshot_name = "snap-" + job_entity.job_id + "-" + serial  # Example : snap-00004-00006

        # -- add log -- #
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} | Job instance ({}) | Creating new snapshot at source disk.".format(
            system_date_time, str(job_entity.job_id), str(active_job.start_time))
        mng_rep.log_replication_job(job_entity.job_id, text)

        self.create_snapshot(src_disk_pool, src_disk_id, snapshot_name)
        src_snapshot_list = self.get_src_snapshots(src_disk_pool, src_disk_id)

        # FIFTH : After create the snapshot , execute --> post_snap_url #
        # ------------------------------------------------------------- #
        if job_entity.post_snap_url:
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job instance ({}) | Calling Post Snapshot Script URL.".format(
                system_date_time, str(job_entity.job_id), str(active_job.start_time))
            mng_rep.log_replication_job(job_entity.job_id, text)

            exe_post_url = self.execute_user_script(job_entity.post_snap_url)

            if not exe_post_url:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Job instance ({}) | Couldn't execute Post Snapshot Script URL : {}.".format(
                    system_date_time, str(job_entity.job_id), str(active_job.start_time), job_entity.post_snap_url)
                mng_rep.log_replication_job(job_entity.job_id, text)


        # Check if : "/opt/petasan/config/replication/" path exists in Remote Cluster #
        try:
            mng_remote_rep.check_replication_folder()
        except Exception as e:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job instance ({}) | {}.".format(
                system_date_time, str(job_entity.job_id), str(active_job.start_time), str(e.message))
            mng_rep.log_replication_job(job_entity.job_id, text)

            # Delete Active Job Instance from Consul #
            # -------------------------------------- #
            consul_api = ConsulAPI()
            consul_api.delete_active_job(job_entity.job_id)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(
                system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)

            return False

        # SIXTH : Create Replication progress files in Source Cluster #
        # ----------------------------------------------------------- #
        # check if job allows compression  #
        allow_compression = False
        if len(job_entity.compression_algorithm) > 0:
            allow_compression = True

        replication_progress_upcomp_file_path, replication_progress_comp_file_path, replication_progress_import_file_path = self.create_progress_files(
            active_job.job_id, allow_compression)

        # SEVENTH : Build the command to run replication #
        # ---------------------------------------------- #
        #  Get destination cluster info  #
        mng_dest_cluster = ManageDestinationCluster()
        dest_cluster = mng_dest_cluster.get_replication_dest_cluster(job_entity.destination_cluster_name)
        decrypted_key = dest_cluster.ssh_private_key

        # Save private key in text file #
        mng_file = ManageTmpFile()

        config_api = ConfigAPI()
        directory_path = config_api.get_replication_tmp_file_path()

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        sshkey_path = config_api.get_replication_sshkey_file_path(active_job.job_id)
        mng_file.create_tmp_file(sshkey_path, decrypted_key)

        # Change mod of 'sshkey_path' file #
        cmd = "chmod 600 {}".format(sshkey_path)
        ret, out, err = exec_command_ex(cmd)

        # -- add log -- #
        command_builder = CommandBuilder()
        cmd = command_builder.build(job_entity, src_snapshot_list, active_job.job_id, dest_cluster, sshkey_path)

        # EIGHTH : Progress Updater Thread #
        # -------------------------------- #
        progress_thread = ProgressUpdaterThread(active_job.job_id, replication_progress_upcomp_file_path,
                                                replication_progress_comp_file_path,
                                                replication_progress_import_file_path)
        progress_thread.start()

        # NINTH : Execute the command #
        # --------------------------- #
        # -- add log -- #
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} | Job instance ({}) | Executing replication job.".format(
            system_date_time, str(job_entity.job_id), str(active_job.start_time))
        mng_rep.log_replication_job(job_entity.job_id, text)

        ret, stdout, stderr = self.execute_replication_cmd(cmd)

        # Delete 'sshkey_path' file #
        mng_file.delete_tmp_file(sshkey_path)

        # IF returncode != 0 #
        if ret != 0:
            system_date_time = str(datetime.datetime.now()).split('.')[0]

            if stderr and ('Connection refused' in stderr):
                text = '{} - Job {} | Job instance ({}) | Error connecting remote cluster , Error = {}'.format(system_date_time, str(job_entity.job_id), str(active_job.start_time), stderr)

            elif stderr and ('Permission denied' in stderr):
                text = '{} - Job {} | Job instance ({}) | Permission denied , Error = {}'.format(system_date_time, str(job_entity.job_id), str(active_job.start_time), stderr)

            elif stderr and ("warning" not in stderr.lower()):
                text = '{} - Job {} | Job instance ({}) | Error = {}'.format(system_date_time, str(job_entity.job_id), str(active_job.start_time), stderr)

            # Check on stderr:
            stderr_str = str(stderr)
            regexp1 = re.compile(r'Exporting')
            regexp2 = re.compile(r'Importing')

            if not (regexp1.search(stderr_str)) and not (regexp2.search(stderr_str)):
                text = '{} - Job {} | Job instance ({}) | Could not run rbd replication command , Error = {}'.format(system_date_time, str(job_entity.job_id), str(active_job.start_time), stderr)

            mng_rep.log_replication_job(job_entity.job_id, text)

            # Delete the active job progress files #
            self.delete_progress_files(active_job.job_id)

            # Delete Active Job Instance from Consul #
            # -------------------------------------- #
            consul_api = ConsulAPI()
            consul_api.delete_active_job(job_entity.job_id)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)

            return False

        # IF returncode == 0 , Check on stderr:
        stderr_str = str(stderr)
        regexp1 = re.compile(r'Exporting')
        regexp2 = re.compile(r'Importing')

        if not (regexp1.search(stderr_str)) and not (regexp2.search(stderr_str)):
            text = '{} - Job {} | Job instance ({}) | Could not run rbd replication command , Error = {}'.format(system_date_time, str(job_entity.job_id), str(active_job.start_time), stderr)
            mng_rep.log_replication_job(job_entity.job_id, text)

            # Delete the active job progress files #
            self.delete_progress_files(active_job.job_id)

            # Delete Active Job Instance from Consul #
            # -------------------------------------- #
            consul_api = ConsulAPI()
            consul_api.delete_active_job(job_entity.job_id)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)

            return False

        # Delete the active job progress files #
        self.delete_progress_files(active_job.job_id)

        # TENTH : Validate the replication process , whether it is succeed or not #
        # ----------------------------------------------------------------------- #
        config_api = ConfigAPI()
        md5_1_file = config_api.get_replication_md5_1_file_path(active_job.job_id)
        md5_2_file = config_api.get_replication_md5_2_file_path(active_job.job_id)

        status = self.validate_replication(job_entity, active_job.job_id)

        if not status:
            # Run replication failure #
            # ----------------------- #
            failure = self.replication_failure(job_entity, "md5_fail")

            # Delete Active Job Instance from Consul #
            # -------------------------------------- #
            consul_api = ConsulAPI()
            consul_api.delete_active_job(job_entity.job_id)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job instance ({}) | Active job has been deleted from Consul.".format(
                system_date_time, str(job_entity.job_id), str(active_job.start_time))
            mng_rep.log_replication_job(job_entity.job_id, text)

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(
                system_date_time, str(job_entity.job_id))
            mng_rep.log_replication_job(job_entity.job_id, text)

            # Delete md5 files from both source and destination clusters #
            # ---------------------------------------------------------- #
            mng_remote_rep.delete_dest_file(md5_2_file)
            self.delete_src_file(md5_1_file)

            return False

        # Replication Success #
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} | Job instance ({}) | Job Succeeded.".format(
            system_date_time, str(job_entity.job_id), str(active_job.start_time))
        mng_rep.log_replication_job(job_entity.job_id, text)


        # ELEVENTH : Delete old snapshot from both source and destination disks (if there is) #
        # ----------------------------------------------------------------------------------- #
        if len(src_snapshot_list) > 1:
            # delete old snapshot from destination disk :
            mng_remote_rep.snapshot_name = src_snapshot_list[0]
            mng_remote_rep.delete_dest_snapshot()

            # delete old snapshot from source disk :
            self.delete_snapshot(src_disk_pool, src_disk_id, src_snapshot_list[0])

        # TWELFTH : Delete Active Job Instance from Consul #
        # ------------------------------------------------ #
        consul_api = ConsulAPI()
        consul_api.delete_active_job(job_entity.job_id)

        # THIRTEENTH : After the completion of replication process #
        # -------------------------------------------------------- #
        if job_entity.post_job_complete:
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job instance ({}) | Calling Post Job Complete URL.".format(
                system_date_time, str(job_entity.job_id), str(active_job.start_time))
            mng_rep.log_replication_job(job_entity.job_id, text)

            exe_post_job = self.execute_user_script(job_entity.post_job_complete)

            if not exe_post_job:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Job instance ({}) | Couldn't execute Post Job Complete URL : {}.".format(
                    system_date_time, str(job_entity.job_id), str(active_job.start_time), job_entity.post_job_complete)
                mng_rep.log_replication_job(job_entity.job_id, text)

        # FINALLY : Delete md5 files from both source and destination clusters #
        # -------------------------------------------------------------------- #
        mng_remote_rep.delete_dest_file(md5_2_file)
        self.delete_src_file(md5_1_file)

        return True


    def replication_failure(self, job_entity, cause):
        mng_rep = ManageReplicationJobs()

        try:
            if job_entity is None:
                # if job entity is deleted #
                logger.error("Error in replication_failure. Can not find replication job.")
                return False

            job_id = job_entity.job_id
            active_job_entity = self.get_active_job(job_entity.job_id)

            if active_job_entity is None:
                # if active job instance is finished or deleted #
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Error in replication_failure. Can not find replication job instance.".format(system_date_time)
                mng_rep.log_replication_job(job_id, text)
                return False

            # Setting data of remote cluster :
            manage_remote_rep = ManageRemoteReplication()
            manage_remote_rep.cluster_name = job_entity.destination_cluster_name
            manage_remote_rep.disk_id = job_entity.destination_disk_id

            # FIRST : Adding a log in job_entity #
            # ---------------------------------- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = ""
            if cause == "md5_fail":
                text = "{} - Job {} | Job instance ({}) | Replication Failed , due to md5 check has been failed.".format(
                    system_date_time, str(job_id), str(active_job_entity.start_time))
            elif cause == "cancel_job":
                text = "{} - Job {} | job instance ({}) | Cancelling job instance , job is unhealthy or cancelled manually.".format(
                    system_date_time, str(job_id), str(active_job_entity.start_time))
            mng_rep.log_replication_job(job_id, text)

            # SECOND : Cleaning after failure #
            # ------------------------------- #
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job instance ({}) | Start cleaning after failure.".format(
                system_date_time, str(job_entity.job_id), str(active_job_entity.start_time))
            mng_rep.log_replication_job(job_entity.job_id, text)
            cleaned = self.start_clean_after_failure(active_job_entity, job_entity)

            if not cleaned:
                return False

            return True

        except Exception as e:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Error in replication_failure. {}".format(system_date_time, str(e.message))
            mng_rep.log_replication_job(job_entity.job_id, text)
            return False


    def start_clean_after_failure(self, active_job_entity, job_entity):
        if job_entity is None:
            # if job entity is deleted #
            logger.error("Error cleaning after failure. Can not find replication job.")
            return False

        mng_rep = ManageReplicationJobs()

        try:
            # Setting data of remote cluster :
            manage_remote_rep = ManageRemoteReplication()
            manage_remote_rep.cluster_name = job_entity.destination_cluster_name
            manage_remote_rep.disk_id = job_entity.destination_disk_id

            last_snap_name = ""

            # CHECK IF SOURCE DISK EXISTS #
            ###############################
            src_disk_meta = mng_rep.get_src_disk_meta(job_entity.source_disk_id)
            if src_disk_meta:
                # FIRST : Get the latest snapshot name of the source disk #
                # ------------------------------------------------------- #
                ceph_api = CephAPI()
                src_disk_id = job_entity.source_disk_id
                src_disk_pool = ceph_api.get_pool_bydisk(src_disk_id)

                # If pool inactive #
                if src_disk_pool is None:
                    logger.error("Job {} | Cannot get pool of disk {}".format(str(job_entity.job_id), str(src_disk_id)))
                    return False

                else:
                    src_snapshot_list = self.get_src_snapshots(src_disk_pool, src_disk_id)

                    if len(src_snapshot_list) > 0:
                        last_snap_name = src_snapshot_list[-1]

                        # SECOND : Delete the latest snapshot from source disk #
                        # --------------------------------------------------- #
                        confirm_delete_src_snapshot = self.delete_snapshot(src_disk_pool, src_disk_id, last_snap_name)

            else:
                # -- add log -- #
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Job instance ({}) | Cannot access source disk.".format(
                    system_date_time, str(job_entity.job_id), str(active_job_entity.start_time))
                mng_rep.log_replication_job(job_entity.job_id, text)
                return False

            # CHECK IF DESTINATION DISK EXISTS #
            ####################################
            try:
                dest_disk_meta = manage_remote_rep.get_disk_meta()
                if dest_disk_meta:
                    # THIRD : Delete the latest snapshot from destination disk #
                    # --------------------------------------------------------- #
                    manage_remote_rep.snapshot_name = last_snap_name
                    dest_snapshot_list = manage_remote_rep.get_dest_snapshots()

                    if len(dest_snapshot_list) > 0 and (last_snap_name in dest_snapshot_list):

                        # FOURTH : Get destination snapshot_list : clear_disk or rollback #
                        # -------------------------------------- #
                        destination_snapshot_ls = manage_remote_rep.get_dest_snapshots()
                        if len(destination_snapshot_ls) == 0:
                            # Clear Destination Disk #
                            try:
                                manage_remote_rep.clear_disk()
                            except Exception as e:
                                system_date_time = str(datetime.datetime.now()).split('.')[0]
                                text = "{} - Job {} | Job instance ({}) | {}.".format(
                                    system_date_time, str(job_entity.job_id), str(active_job_entity.start_time), str(e.message))
                                mng_rep.log_replication_job(job_entity.job_id, text)
                                return False

                        elif len(destination_snapshot_ls) == 1:
                            # Rollback Destination Disk to this Snapshot #
                            manage_remote_rep.snapshot_name = destination_snapshot_ls[0]
                            manage_remote_rep.rollback_dest_snapshot()

            except ReplicationException as e:
                if e.id == ReplicationException.CONNECTION_TIMEOUT:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Cannot access destination disk | Connection Timed Out , {}".format(
                        system_date_time, str(job_entity.job_id), str(e.message))
                    mng_rep.log_replication_job(job_entity.job_id, text)

                elif e.id == ReplicationException.CONNECTION_REFUSED:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Cannot access destination disk | Connection Refused , {}".format(
                        system_date_time, str(job_entity.job_id), str(e.message))
                    mng_rep.log_replication_job(job_entity.job_id, text)

                elif e.id == ReplicationException.PERMISSION_DENIED:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Cannot access destination disk | Permission Denied , {}".format(
                        system_date_time, str(job_entity.job_id), str(e.message))
                    mng_rep.log_replication_job(job_entity.job_id, text)

                return False

            except PoolException as e:
                if e.id == PoolException.CANNOT_GET_POOL:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Destination disk not found , {}".format(system_date_time, str(job_entity.job_id), str(e.message))
                    mng_rep.log_replication_job(job_entity.job_id, text)

                return False

            except DiskListException as e:
                if e.id == DiskListException.DISK_NOT_FOUND:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Destination disk not found , {}".format(system_date_time, str(job_entity.job_id), str(e.message))
                    mng_rep.log_replication_job(job_entity.job_id, text)

                return False

            except CephException as e:
                if e.id == CephException.GENERAL_EXCEPTION:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Destination disk not found , {}".format(system_date_time, str(job_entity.job_id), str(e.message))
                    mng_rep.log_replication_job(job_entity.job_id, text)

                return False

            except MetadataException as e:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Destination disk not found , {}".format(system_date_time, str(job_entity.job_id), str(e.message))
                mng_rep.log_replication_job(job_entity.job_id, text)

                return False

            except Exception as e:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Cannot access destination disk | General Exception , {}".format(
                    system_date_time, str(job_entity.job_id), str(e.message))
                mng_rep.log_replication_job(job_entity.job_id, text)

                return False

            return True

        except Exception as e:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Error cleaning after failure. {}".format(system_date_time, str(e.message))
            mng_rep.log_replication_job(job_entity.job_id, text)
            return False

    # ---------------------------------------- METADATA ----------------------------------------- #
    ###############################################################################################

    # Getting disk's metadata for all "Local Cluster" disks on all pools (DiskMeta Objects):
    def get_disks_meta(self):
        local_disks_metadata = ManageDisk().get_disks_meta()
        return local_disks_metadata

    # ---------------------------------------- SNAPSHOTS ---------------------------------------- #
    ###############################################################################################

    # Giving pool_name and disk_id of a "Local Cluster" disk , get all image snapshots :
    def get_src_snapshots(self, pool_name, disk_id):
        ceph_api = CephAPI()
        image_name = "image-" + disk_id
        disk_snapshots_ls = ceph_api.get_disk_snapshots(pool_name, image_name)
        return disk_snapshots_ls

    # Giving pool_name and disk_id of a "Local Cluster" disk , create a new snapshot for this image :
    def create_snapshot(self, pool_name, disk_id, snapshot_name):
        ceph_api = CephAPI()
        image_name = "image-" + disk_id
        confirm = ceph_api.create_snapshot(pool_name, image_name, snapshot_name)
        return confirm

    # Giving pool_name , disk_id and a snapshot_name , delete the snapshot :
    def delete_snapshot(self, pool_name, disk_id, snapshot_name):
        ceph_api = CephAPI()
        image_name = "image-" + disk_id
        confirm = ceph_api.delete_snapshot(pool_name, image_name, snapshot_name)
        return confirm

    # ------------------------------------------ FILES ------------------------------------------ #
    ###############################################################################################

    def delete_src_file(self, file_name):
        cmd = "rm -f {}".format(file_name)
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            logger.error('Cannot delete file : {} , error : {}'.format(file_name, stderr))
            return False
        return True

    def read_file(self, file_name):
        cmd = "cat {}".format(file_name)
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            if 'No such file or directory' in stderr:
                logger.error('Error in cmd : {} , error : {}'.format(cmd, stderr))

            logger.error('Error in cmd : {} , error : {}'.format(cmd, stderr))

        output = stdout
        return output

    def create_progress_files(self, active_job_id, allow_compression):
        # home = expanduser('~')
        config_api = ConfigAPI()
        replication_tmp_file_path = config_api.get_replication_tmp_file_path()
        replication_progress_comp_file_path = config_api.get_replication_progress_comp_file_path(active_job_id)
        replication_progress_upcomp_file_path = config_api.get_replication_progress_uncomp_file_path(active_job_id)
        replication_progress_import_file_path = config_api.get_replication_progress_import_file_path(active_job_id)

        # Check if : "/opt/petasan/config/replication/" path exists :
        if not os.path.exists(replication_tmp_file_path):
            os.makedirs(replication_tmp_file_path)

        # Create uncompressed file :
        uncomp_file = open(replication_progress_upcomp_file_path, 'a+')
        uncomp_file.close()

        # Create export progress file :
        export_file = open(replication_progress_import_file_path, 'a+')
        export_file.close()

        if allow_compression:
            # Create compressed file:
            comp_file = open(replication_progress_comp_file_path, 'a+')
            comp_file.close()
        else:
            replication_progress_comp_file_path = ""

        return replication_progress_upcomp_file_path, replication_progress_comp_file_path, replication_progress_import_file_path

    # ------------------------------------ REP. ACTIVE JOBS ------------------------------------- #
    ###############################################################################################

    def get_active_job(self, job_id):
        consul_api = ConsulAPI()
        active_job = consul_api.get_replication_active_job(job_id)
        return active_job

    def update_active_job(self, active_job):
        consul_api = ConsulAPI()
        confirm = consul_api.update_replication_active_job(active_job)
        return confirm

    def cancel_active_job(self, active_job_id):
        manage_rep = ManageReplicationJobs()
        mng_remote_rep = ManageRemoteReplication()

        try:
            rep_job = active_job_id.split('-')
            rep_job_id = rep_job[0]

            # FIRST : get replication job :
            job_entity = manage_rep.get_replication_job(rep_job_id)

            if job_entity is None:
                # if job entity is deleted #
                logger.error("Error in canceling job. Can not find replication job {}".format(rep_job_id))
                return False

            # SECOND : get active replication job :
            active_job = self.get_active_job(rep_job_id)

            if active_job is None:
                # if active job instance is finished or deleted #
                if job_entity is None:
                    logger.warning("Error in canceling job. Can not find replication job instance {}".format(active_job_id))
                else:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Error in canceling job. Can not find replication job instance {}".format(system_date_time, active_job_id)
                    manage_rep.log_replication_job(rep_job_id, text)
                return False

            mng_remote_rep.cluster_name = job_entity.destination_cluster_name

            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job instance ({}) | Checking on pid : {}".format(system_date_time,
                                                                                                 str(rep_job_id),
                                                                                                 str(active_job.start_time),
                                                                                                 active_job.pid)
            manage_rep.log_replication_job(rep_job_id, text)

            # Kill Previous Active Job Processes Destination Cluster #
            # ------------------------------------------------------ #
            #  Get destination cluster info  #
            mng_dest_cluster = ManageDestinationCluster()
            dest_cluster = mng_dest_cluster.get_replication_dest_cluster(job_entity.destination_cluster_name)
            dest_user_name = dest_cluster.user_name
            dest_cluster_ip = dest_cluster.remote_ip
            decrypted_key = dest_cluster.ssh_private_key

            # Save private key in text file #
            mng_file = ManageTmpFile()

            config_api = ConfigAPI()
            directory_path = config_api.get_replication_tmp_file_path()

            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            sshkey_path = config_api.get_replication_sshkey_file_path(active_job_id)
            mng_file.create_tmp_file(sshkey_path, decrypted_key)

            # Change mod of 'sshkey_path' file #
            cmd = "chmod 600 {}".format(sshkey_path)
            ret, out, err = exec_command_ex(cmd)

            # Run script remotely at destination cluster as follows #
            # ----------------------------------------------------- #
            script_file = ConfigAPI().get_replication_kill_job_processes_file_path()
            arg1 = "--active_job_id"

            # Define cmd command
            cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} {}"'.format(sshkey_path, dest_user_name,
                                                                                  dest_cluster_ip, script_file,
                                                                                  arg1, active_job_id)

            ret, stdout, stderr = exec_command_ex(cmd)

            # Delete 'sshkey_path' file #
            mng_file.delete_tmp_file(sshkey_path)

            if ret != 0:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster.'.format(system_date_time, str(rep_job_id), str(active_job.start_time))

                if stderr and ('Connection refused' in stderr):
                    text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster | Connection refused , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stderr))

                elif stderr and ('Permission denied' in stderr):
                    text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster | Permission denied , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stderr))

                elif stderr and ("warning" not in stderr.lower()):
                    text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stderr))

                # else:
                #     text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stderr))

                manage_rep.log_replication_job(rep_job_id, text)

            if stdout and ('Error' in stdout):
                text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stdout))
                manage_rep.log_replication_job(rep_job_id, text)

            if stderr and ("warning" not in stderr.lower()):
                text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stderr))
                manage_rep.log_replication_job(rep_job_id, text)

            # Kill Previous Active Job Processes (Children) in Source Cluster #
            # --------------------------------------------------------------- #
            script_file = ConfigAPI().get_replication_kill_job_processes_file_path()
            arg1 = "--active_job_id"

            # Define cmd command
            cmd = '{} {} {}'.format(script_file, arg1, active_job_id)

            ret, stdout, stderr = exec_command_ex(cmd)
            if ret != 0:
                if stderr:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Job instance ({}) | Cannot kill job process children , pid = {}".format(
                        system_date_time, str(rep_job_id), str(active_job.start_time), active_job.pid)
                    manage_rep.log_replication_job(rep_job_id, text)

            # Kill Previous Active Job Processes (Parent) in Source Cluster #
            # ------------------------------------------------------------- #
            if self.check_pid(int(active_job.pid)):
                try:
                    parent = psutil.Process(int(active_job.pid))
                    parent.kill()
                except:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = "{} - Job {} | Job instance ({}) | Cannot kill job process , pid = {}".format(
                        system_date_time, str(rep_job_id), str(active_job.start_time), active_job.pid)
                    manage_rep.log_replication_job(rep_job_id, text)
                    return False

            # Run replication failure #
            # ----------------------- #
            clean = self.replication_failure(job_entity, "cancel_job")

            # Add job_entity to consul in key (PetaSAN/Replication/Failed_Jobs/job_id) #
            # ------------------------------------------------------------------------ #
            consul_api = ConsulAPI()
            result = consul_api.add_replication_failed_job(job_entity)

            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job Failed.".format(
                system_date_time, str(rep_job_id))
            manage_rep.log_replication_job(rep_job_id, text)

            if not clean:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = '{} - Job {} | Job instance ({}) | Error cleaning after replication_failure.'.format(
                    system_date_time, str(rep_job_id.job_id), str(active_job.start_time))
                manage_rep.log_replication_job(rep_job_id, text)
                return False

            # Delete Active Job Instance from Consul #
            # -------------------------------------- #
            consul_api.delete_active_job(rep_job_id)

            # Delete the active job progress files #
            # ------------------------------------ #
            self.delete_progress_files(active_job_id)

            # Delete md5 files #
            # ---------------- #
            config_api = ConfigAPI()
            md5_1_file = config_api.get_replication_md5_1_file_path(active_job.job_id)
            md5_2_file = config_api.get_replication_md5_2_file_path(active_job.job_id)
            mng_remote_rep.delete_dest_file(md5_2_file)
            self.delete_src_file(md5_1_file)

            return True

        except Exception as e:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Error in cancelling active job. {}".format(system_date_time, str(e.message))
            rep_job = active_job_id.split('-')
            rep_job_id = rep_job[0]
            manage_rep.log_replication_job(rep_job_id, text)
            return False


    def force_cancel_active_job(self, active_job_id):
        manage_rep = ManageReplicationJobs()
        mng_remote_rep = ManageRemoteReplication()

        rep_job = active_job_id.split('-')
        rep_job_id = rep_job[0]

        # FIRST : get replication job :
        job_entity = manage_rep.get_replication_job(rep_job_id)

        # SECOND : get active replication job :
        active_job = self.get_active_job(rep_job_id)

        if job_entity is None:
            # if job entity is deleted #
            logger.warning("Warning in canceling job. Can not find replication job {}".format(rep_job_id))

        if active_job is None:
            # if active job instance is finished before you confirm deleting , or deleted #
            if job_entity is None:
                logger.warning("Warning in canceling job. Can not find replication job instance {}".format(active_job_id))
            else:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Warning in canceling job. Can not find replication job instance {}".format(system_date_time, active_job_id)
                manage_rep.log_replication_job(rep_job_id, text)
            return True

        if job_entity and active_job:
            try:
                mng_remote_rep.cluster_name = job_entity.destination_cluster_name

                # Kill Previous Active Job Processes Destination Cluster #
                # ------------------------------------------------------ #
                #  Get destination cluster info  #
                mng_dest_cluster = ManageDestinationCluster()
                dest_cluster = mng_dest_cluster.get_replication_dest_cluster(job_entity.destination_cluster_name)
                dest_user_name = dest_cluster.user_name
                dest_cluster_ip = dest_cluster.remote_ip
                decrypted_key = dest_cluster.ssh_private_key

                # Save private key in text file #
                mng_file = ManageTmpFile()

                config_api = ConfigAPI()
                directory_path = config_api.get_replication_tmp_file_path()

                if not os.path.exists(directory_path):
                    os.makedirs(directory_path)

                sshkey_path = config_api.get_replication_sshkey_file_path(active_job_id)
                mng_file.create_tmp_file(sshkey_path, decrypted_key)

                # Change mod of 'sshkey_path' file #
                cmd = "chmod 600 {}".format(sshkey_path)
                ret, out, err = exec_command_ex(cmd)

                # Run script remotely at destination cluster as follows #
                # ----------------------------------------------------- #
                script_file = ConfigAPI().get_replication_kill_job_processes_file_path()
                arg1 = "--active_job_id"

                # Define cmd command
                cmd = 'ssh -o StrictHostKeyChecking=no -i {} {}@{} "{} {} {}"'.format(sshkey_path, dest_user_name,
                                                                                      dest_cluster_ip, script_file,
                                                                                      arg1, active_job_id)

                ret, stdout, stderr = exec_command_ex(cmd)

                # Delete 'sshkey_path' file #
                mng_file.delete_tmp_file(sshkey_path)

                if ret != 0:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster.'.format(system_date_time, str(rep_job_id), str(active_job.start_time))

                    if stderr and ('Connection refused' in stderr):
                        text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster | Connection refused , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stderr))

                    elif stderr and ('Permission denied' in stderr):
                        text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster | Permission denied , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stderr))

                    elif stderr and ("warning" not in stderr.lower()):
                        text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stderr))

                    # else:
                    #     text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stderr))

                    manage_rep.log_replication_job(rep_job_id, text)

                if stdout and ('Error' in stdout):
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stdout))
                    manage_rep.log_replication_job(rep_job_id, text)

                if stderr and ("warning" not in stderr.lower()):
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = '{} - Job {} | Job instance ({}) | Seeing if there is job processes at Destination Cluster , Error = {}'.format(system_date_time, str(rep_job_id), str(active_job.start_time), str(stderr))
                    manage_rep.log_replication_job(rep_job_id, text)

                # Kill Previous Active Job Processes (Children) in Source Cluster #
                # --------------------------------------------------------------- #
                script_file = ConfigAPI().get_replication_kill_job_processes_file_path()
                arg1 = "--active_job_id"

                # Define cmd command
                cmd = '{} {} {}'.format(script_file, arg1, active_job_id)

                ret, stdout, stderr = exec_command_ex(cmd)
                if ret != 0:
                    if stderr:
                        system_date_time = str(datetime.datetime.now()).split('.')[0]
                        text = "{} - Job {} | Job instance ({}) | Cannot kill job process children , pid = {}".format(
                            system_date_time, str(rep_job_id), str(active_job.start_time), active_job.pid)
                        manage_rep.log_replication_job(rep_job_id, text)

                # Kill Previous Active Job Processes (Parent) in Source Cluster #
                # ------------------------------------------------------------- #
                if self.check_pid(int(active_job.pid)):
                    try:
                        parent = psutil.Process(int(active_job.pid))
                        parent.kill()
                    except:
                        system_date_time = str(datetime.datetime.now()).split('.')[0]
                        text = "{} - Job {} | Job instance ({}) | Cannot kill job process , pid = {}".format(
                            system_date_time, str(rep_job_id), str(active_job.start_time), active_job.pid)
                        manage_rep.log_replication_job(rep_job_id, text)

                # Delete the active job progress files #
                # ------------------------------------ #
                self.delete_progress_files(active_job_id)

                # Delete md5 files #
                # ---------------- #
                config_api = ConfigAPI()
                md5_1_file = config_api.get_replication_md5_1_file_path(active_job.job_id)
                md5_2_file = config_api.get_replication_md5_2_file_path(active_job.job_id)
                mng_remote_rep.delete_dest_file(md5_2_file)
                self.delete_src_file(md5_1_file)

                # Run replication failure #
                # ----------------------- #
                replication_job = manage_rep.get_replication_job(rep_job_id)
                clean = self.replication_failure(replication_job, "cancel_job")

                if not clean:
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    text = '{} - Job {} | Job instance ({}) | Error cleaning after replication_failure.'.format(
                        system_date_time, str(rep_job_id), str(active_job.start_time))
                    manage_rep.log_replication_job(rep_job_id, text)

            except Exception as e:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Error in cancelling active job. {}".format(system_date_time, str(e.message))
                rep_job = active_job_id.split('-')
                rep_job_id = rep_job[0]
                manage_rep.log_replication_job(rep_job_id, text)

        # Delete Active Job Instance from Consul #
        # -------------------------------------- #
        consul_api = ConsulAPI()
        consul_api.delete_active_job(rep_job_id)

        if job_entity is None :
            # if job entity is deleted #
            logger.warning("Job {} | Job instance has been canceled.".format(rep_job_id))

        else:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Job instance ({}) has been canceled.".format(system_date_time, str(rep_job_id), str(active_job.start_time))
            manage_rep.log_replication_job(rep_job_id, text)

        return True


    def check_pid(self, pid):
        """ Check For the existence of a unix pid. """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def is_job_healthy(self, active_job_entity):
        # get process id of the active job as :
        pid = active_job_entity.pid
        if pid > 0:
            # check job progress :
            progress_status = self.is_job_running(active_job_entity)
            if progress_status:
                return True
            return False
        else:
            return False

    def is_job_running(self, active_job_entity):
        # within 5 min.s , read progress value (number of transferred bytes) of active_job_entity every 10 sec.s
        # total = 5 min.s = 5x60 = 300 sec.s

        transferred_bytes_before = active_job_entity.uncompressed_transferred_bytes

        active_job_id = active_job_entity.job_id.split("-")
        rep_job_id = active_job_id[0]

        counter = 0
        while counter < 30:
            active_job = self.get_active_job(rep_job_id)

            # See if active_job_entity is finished ( not existed in Consul ) #
            if active_job is None:
                # return True --> will not run the new job instance #
                return None

            transferred_bytes_after = active_job.uncompressed_transferred_bytes

            # check if there is a change :
            if transferred_bytes_before != transferred_bytes_after:
                return True
            sleep(10)  # 10 sec.s
            counter += 1
        return False

    def execute_user_script(self, url):
        # Run web service from it's path url as :
        cmd = "curl {}".format(url)
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret == 0:
            if not stderr:
                return True
        return True

    def execute_replication_cmd(self, cmd):
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             executable="/bin/bash")  # .stdout.read()
        p_id = p.pid
        stdout, stderr = p.communicate()
        ret = p.returncode
        return ret, stdout, stderr

    def get_next_snap_serial(self, snapshot_list):
        if len(snapshot_list) == 0:
            next_serial = '00001'
        else:
            last_snap_name = snapshot_list[-1]
            ls = last_snap_name.split('-')
            serial = ls[2]
            serial_number = int(serial)
            next_serial_number = serial_number + 1
            next_serial = "{:05d}".format(next_serial_number)

        return next_serial

    def validate_replication(self, job_entity, active_job_id):
        ls = active_job_id.split('-')
        rep_job_id = ls[0]

        if job_entity is None:
            # if job entity is deleted #
            logger.error("Error in validating replication job. Can not find replication job.")
            return False

        config_api = ConfigAPI()
        md5_1_file = config_api.get_replication_md5_1_file_path(active_job_id)
        md5_2_file = config_api.get_replication_md5_2_file_path(active_job_id)

        # read md5 value of source disk
        src_md5 = self.read_file(md5_1_file)

        # read first md5 value of destination disk
        manage_remote_rep = ManageRemoteReplication()
        manage_remote_rep.cluster_name = job_entity.destination_cluster_name
        manage_remote_rep.disk_id = job_entity.destination_disk_id

        dest_md5 = manage_remote_rep.read_dest_file(md5_2_file)

        if src_md5 == dest_md5:
            return True

        else:
            return False

    def delete_progress_files(self, active_job_id):
        config_api = ConfigAPI()
        replication_progress_comp_file_path = config_api.get_replication_progress_comp_file_path(active_job_id)
        replication_progress_upcomp_file_path = config_api.get_replication_progress_uncomp_file_path(active_job_id)
        replication_progress_import_file_path = config_api.get_replication_progress_import_file_path(active_job_id)

        self.delete_src_file(replication_progress_upcomp_file_path)
        self.delete_src_file(replication_progress_import_file_path)
        self.delete_src_file(replication_progress_comp_file_path)


    def kill_job_processes(self, active_job_id):
        # Add a log in job_entity :
        mng_rep = ManageReplicationJobs()
        ls = active_job_id.split('-')
        rep_job_id = ls[0]
        active_job_entity = self.get_active_job(rep_job_id)

        if active_job_entity :
            replication_processes = {'/opt/petasan/scripts/backups/pipe_reader.py', 'rbd import-diff', 'rbd export-diff'}

            active_processes = []

            for process in psutil.process_iter():
                pinfo = process.as_dict(attrs=['pid', 'name', 'username', 'cmdline'])

                for item in pinfo['cmdline']:
                    for name in replication_processes:
                        if name in item:
                            # print(pinfo['cmdline'])
                            active_processes.append(process)
                            continue

            rep_job_ls = active_job_id.split('-')
            time_stamp = rep_job_ls[1]

            for process in active_processes:
                pinfo = process.as_dict(attrs=['pid', 'name', 'username', 'cmdline'])

                for item in pinfo['cmdline']:
                    if time_stamp in item:
                        # logger.info(pinfo['cmdline'])
                        try:
                            process.kill()

                        except psutil.NoSuchProcess as e:
                            text = "Kill job processes - process with PID {} , doesn't or no longer exists.".format(pinfo['pid'])
                            logger.error(text)
                            continue

                        except psutil.AccessDenied as e:
                            text = "Kill job processes - permission to perform an action (kill process) is denied."
                            logger.error(text)
                            continue

                        except psutil.Error as e:
                            text = "Kill job processes - General psutil exception , {}".format(str(e.message))
                            logger.error(text)
                            continue
