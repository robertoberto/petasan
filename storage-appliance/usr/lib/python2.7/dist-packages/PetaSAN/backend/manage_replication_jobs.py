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

import datetime
from flask import json
from PetaSAN.core.ceph import ceph_disk as ceph_disk
from PetaSAN.backend.manage_node import ManageNode
from PetaSAN.backend.replication.manage_disk_replication_info import ManageDiskReplicationInfo
from PetaSAN.backend.replication.manage_remote_replication import ManageRemoteReplication
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.CustomException import ReplicationException, DiskListException, PoolException, CephException, \
    MetadataException
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.common.log import logger
from PetaSAN.core.entity.disk_info import DiskMeta


class ManageReplicationJobs:
    def __init__(self):
        pass

    ####################################################################################################################
    # Get all Replication Jobs with 'started' or 'stopped' status :
    def get_replication_jobs(self):
        consul_api = ConsulAPI()
        jobs = consul_api.get_replication_jobs()
        return jobs

    ####################################################################################################################
    # Giving the job_id , get the Replication Job :
    def get_replication_job(self, job_id):
        consul_api = ConsulAPI()
        job_entity = consul_api.get_replication_job(job_id)
        return job_entity

    ####################################################################################################################
    # Giving the job_id , get the Replication Job Log :
    def get_replication_job_log(self, job_id):
        consul_api = ConsulAPI()
        logs_list = []
        logs_list_json = consul_api.get_replication_job_log(job_id)
        if len(logs_list_json) < 1:
            return logs_list
        logs_list = json.loads(logs_list_json)
        return logs_list

    ####################################################################################################################
    # Giving the job_id and a log text , save the Replication Job Log :
    def log_replication_job(self, job_id, text):
        consul_api = ConsulAPI()

        # Check if Replication Job is existed in Consul
        job_entity = self.get_replication_job(job_id)

        if job_entity is None:
            # if job entity is deleted #
            logger.warning("The job {} does not exist --- {}".format(job_id, str(text)))

        else:
            logs_list = self.get_replication_job_log(job_id)
            logs_list.append(str(text))

            if len(logs_list) > 200:
                del logs_list[0]

            consul_api.log_replication_job(job_id, json.dumps(logs_list))

    ####################################################################################################################
    # Starting a Replication Job ( New Job or Stopped Job ) :
    def start_replication_job(self, job_entity):
        # Get destination disk metadata :
        manage_remote_rep = ManageRemoteReplication()
        manage_remote_rep.cluster_name = job_entity.destination_cluster_name
        manage_remote_rep.disk_id = job_entity.destination_disk_id

        # FIRST : Getting metadata destination disk #           Check if destination disk exists
        try:
            dest_meta_dict = manage_remote_rep.get_disk_meta()
            dest_disk_meta_obj = DiskMeta(dest_meta_dict)

            if dest_meta_dict:
                # Check if destination "replication-info" is not empty  // means disk is replication enabled // :
                dest_replication_info = dest_disk_meta_obj.replication_info

                if dest_replication_info:
                    # Change the job status to be "started" :
                    job_entity.status = "started"

                    # Save new job in consul or edit status of existed job :
                    consul_api = ConsulAPI()
                    consul_api.update_replication_job(job_entity)  # Saving new job in Consul or Updating stopped job

                    # Call script to build crontab :
                    self.start_node_service()

                    # Define a text to add in job's log as : "system_date_time : job {job_id} has been started"
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    job_id = job_entity.job_id
                    text = "{} - Job {} has been started.".format(system_date_time, job_id)

                    # Saving log in Consul :
                    self.log_replication_job(job_id, text)

                else:
                    # Define a text to add in job's log as : "system_date_time : job {job_id} has been failed to start , destination disk isn't replication enabled"
                    system_date_time = str(datetime.datetime.now()).split('.')[0]
                    job_id = job_entity.job_id
                    text = "{} - Job {} has been failed to start , destination disk doesn't have replication info.".format(
                        system_date_time, job_id)
                    self.log_replication_job(job_id, text)


        except ReplicationException as e:
            if e.id == ReplicationException.CONNECTION_TIMEOUT:
                logger.error("Job {} | Cannot access destination disk | Connection Timed Out , {}".format(str(job_entity.job_id), str(e.message)))

            elif e.id == ReplicationException.CONNECTION_REFUSED:
                logger.error("Job {} | Cannot access destination disk | Connection Refused , {}".format(str(job_entity.job_id), str(e.message)))

            elif e.id == ReplicationException.PERMISSION_DENIED:
                logger.error("Job {} | Cannot access destination disk | Permission Denied , {}".format(str(job_entity.job_id), str(e.message)))

            elif e.id == ReplicationException.GENERAL_EXCEPTION:
                logger.error("Job {} | Cannot access destination disk | {}".format(str(job_entity.job_id), str(e.message)))

        except PoolException as e:
            if e.id == PoolException.CANNOT_GET_POOL:
                logger.error("Job {} | Destination disk not found | {}".format(str(job_entity.job_id), str(e.message)))

        except DiskListException as e:
            if e.id == DiskListException.DISK_NOT_FOUND:
                logger.error("Job {} | Destination disk not found | {}".format(str(job_entity.job_id), str(e.message)))

        except CephException as e:
                if e.id == CephException.GENERAL_EXCEPTION:
                    logger.error("Job {} | Destination disk not found | {}".format(str(job_entity.job_id), str(e.message)))

        except MetadataException as e:
            logger.error("Job {} | Destination disk not found | {}".format(str(job_entity.job_id), str(e.message)))

        except Exception as e:
            logger.error("Job {} | Cannot access destination disk | {}".format(str(job_entity.job_id), str(e.message)))

    ####################################################################################################################
    # Stopping a Replication Job ( A Started Job ) :
    def stop_replication_job(self, job_entity):
        job_id = job_entity.job_id

        # Setting data of remote cluster #
        # ------------------------------ #
        manage_remote_rep = ManageRemoteReplication()
        manage_remote_rep.cluster_name = job_entity.destination_cluster_name
        manage_remote_rep.disk_id = job_entity.destination_disk_id

        # FIRST : Getting metadata destination disk #           Check if destination disk exists
        try:
            dest_disk_meta = manage_remote_rep.get_disk_meta()
            # dest_disk_meta_obj = DiskMeta(dest_disk_meta)

            if dest_disk_meta:
                # Delete all Destination Disk Snapshots :
                manage_remote_rep.delete_dest_snapshots()

        except ReplicationException as e:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Cannot access destination disk.".format(system_date_time, job_id)

            if e.id == ReplicationException.CONNECTION_TIMEOUT:
                text = "{} - Job {} | Cannot access destination disk | Connection Timed Out , {}".format(system_date_time, job_id, str(e.message))

            elif e.id == ReplicationException.CONNECTION_REFUSED:
                text = "{} - Job {} | Cannot access destination disk | Connection Refused , {}".format(system_date_time, job_id, str(e.message))

            elif e.id == ReplicationException.PERMISSION_DENIED:
                text = "{} - Job {} | Cannot access destination disk | Permission Denied , {}".format(system_date_time, job_id, str(e.message))

            elif e.id == ReplicationException.GENERAL_EXCEPTION:
                text = "{} - Job {} | Cannot access destination disk | {}".format(system_date_time, job_id, str(e.message))

            self.log_replication_job(job_id, text)

        except PoolException as e:
            if e.id == PoolException.CANNOT_GET_POOL:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Destination disk not found | {}".format(system_date_time, job_id, str(e.message))
                self.log_replication_job(job_id, text)

        except DiskListException as e:
            if e.id == DiskListException.DISK_NOT_FOUND:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Destination disk not found | {}".format(system_date_time, job_id, str(e.message))
                self.log_replication_job(job_id, text)

        except CephException as e:
            if e.id == CephException.GENERAL_EXCEPTION:
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Destination disk not found | {}".format(system_date_time, job_id, str(e.message))
                self.log_replication_job(job_id, text)

        except MetadataException as e:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Destination disk not found | {}".format(system_date_time, job_id, str(e.message))
            self.log_replication_job(job_id, text)

        except Exception as e:
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            job_id = job_entity.job_id
            text = "{} - Job {} | Cannot access destination disk | General Exception , {}".format(system_date_time, job_id, str(e.message))
            self.log_replication_job(job_id, text)


        # SECOND : Getting metadata source disk :           Check if source disk exists
        src_disk_id = job_entity.source_disk_id

        try:
            src_disk_meta = self.get_src_disk_meta(src_disk_id)

            if src_disk_meta:
                # Delete all Source Disk Snapshots :
                ceph_api = CephAPI()
                pool_name = ceph_api.get_pool_bydisk(job_entity.source_disk_id)

                # If pool inactive #
                if pool_name is None:
                    logger.error("Job {} | Cannot get pool of disk {}".format(str(job_entity.job_id), str(job_entity.source_disk_id)))
                else:
                    # rep_handler = ReplicationHandler()
                    self.delete_snapshots(pool_name, job_entity.source_disk_id)

            else:
                # -- add log -- #
                system_date_time = str(datetime.datetime.now()).split('.')[0]
                text = "{} - Job {} | Cannot access source disk.".format(system_date_time, job_id)
                self.log_replication_job(job_id, text)

        except Exception as e:
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Cannot access source disk. {}".format(system_date_time, job_id, str(e.message))
            self.log_replication_job(job_id, text)

        # Edit status of Replication Job :
        consul_api = ConsulAPI()
        job_entity.status = "stopped"  # Changing the job status to be "stopped"
        consul_api.update_replication_job(job_entity)  # Updating the job

        # Call script to build crontab :
        self.start_node_service()

        # Define a text to add in job's log as : "system_date_time : job {job_id} has been stopped"
        system_date_time = str(datetime.datetime.now()).split('.')[0]
        text = "{} - Job {} has been stopped.".format(system_date_time, job_id)

        # Saving log in Consul :
        self.log_replication_job(job_id, text)

    ####################################################################################################################
    # Deleting a Replication Job :
    def delete_replication_job(self, job_entity):
        # Setting data of remote cluster #
        # ------------------------------ #
        manage_remote_rep = ManageRemoteReplication()
        manage_remote_rep.cluster_name = job_entity.destination_cluster_name
        manage_remote_rep.disk_id = job_entity.destination_disk_id

        # FIRST : Getting metadata destination disk #           Check if destination disk exists
        try:
            dest_disk_meta = manage_remote_rep.get_disk_meta()
            # dest_disk_meta_obj = DiskMeta(dest_disk_meta)

            if dest_disk_meta:
                # Clear "replication_info" from Destination Disk :
                dest_check = manage_remote_rep.delete_replication_info()

                # Delete all Destination Disk Snapshots :
                manage_remote_rep.delete_dest_snapshots()

        except ReplicationException as e:
            if e.id == ReplicationException.CONNECTION_TIMEOUT:
                logger.error("Job {} | Cannot access destination disk | Connection Timed Out , {}".format(str(job_entity.job_id), str(e.message)))

            elif e.id == ReplicationException.CONNECTION_REFUSED:
                logger.error("Job {} | Cannot access destination disk | Connection Refused , {}".format(str(job_entity.job_id), str(e.message)))

            elif e.id == ReplicationException.PERMISSION_DENIED:
                logger.error("Job {} | Cannot access destination disk | Permission Denied , {}".format(str(job_entity.job_id), str(e.message)))

            elif e.id == ReplicationException.GENERAL_EXCEPTION:
                logger.error("Job {} | Cannot access destination disk | {}".format(str(job_entity.job_id), str(e.message)))

        except PoolException as e:
            if e.id == PoolException.CANNOT_GET_POOL:
                logger.error("Job {} | Destination disk not found | {}".format(str(job_entity.job_id), str(e.message)))

        except DiskListException as e:
            if e.id == DiskListException.DISK_NOT_FOUND:
                logger.error("Job {} | Destination disk not found | {}".format(str(job_entity.job_id), str(e.message)))

        except CephException as e:
                if e.id == CephException.GENERAL_EXCEPTION:
                    logger.error("Job {} | Destination disk not found | {}".format(str(job_entity.job_id), str(e.message)))

        except MetadataException as e:
            logger.error("Job {} | Destination disk not found | {}".format(str(job_entity.job_id), str(e.message)))

        except Exception as e:
            logger.error("Job {} | Cannot access destination disk | {}".format(str(job_entity.job_id), str(e.message)))


        # rep_handler = ReplicationHandler()

        # SECOND : Getting metadata source disk :           Check if source disk exists
        src_disk_id = job_entity.source_disk_id

        try:
            src_disk_meta = self.get_src_disk_meta(src_disk_id)

            if src_disk_meta:
                # Clear "replication_info" from Source Disk :
                mng_rep_info = ManageDiskReplicationInfo()
                src_check = mng_rep_info.delete_replication_info(src_disk_meta)

                # Delete all Source Disk Snapshots :
                ceph_api = CephAPI()
                pool_name = ceph_api.get_pool_bydisk(job_entity.source_disk_id)

                # If pool inactive #
                if pool_name is None:
                    logger.error("Job {} | Cannot get pool of disk {}".format(str(job_entity.job_id), str(job_entity.source_disk_id)))
                else:
                    self.delete_snapshots(pool_name, job_entity.source_disk_id)

            else:
                logger.error("Job {} | Cannot access source disk ...".format(str(job_entity.job_id)))

        except Exception as e:
            # -- add log -- #
            system_date_time = str(datetime.datetime.now()).split('.')[0]
            text = "{} - Job {} | Cannot access source disk. {}".format(system_date_time, str(job_entity.job_id), str(e.message))
            self.log_replication_job(job_entity.job_id, text)

        # Delete Replication Job + Delete Replication Job Log --> from consul :
        consul_api = ConsulAPI()
        consul_api.delete_replication_job(job_entity)  # Deleting Replication job from Consul
        consul_api.delete_replication_log(job_entity)  # Deleting Replication job log from Consul

        # Define a text to add in Node's log as : "The replication job {job_id} has been deleted"
        logger.info("The replication job {} has been deleted.".format(job_entity.job_id))

        # Call script to build crontab :
        self.start_node_service()

    ####################################################################################################################
    # Adding a Replication Job :
    def add_replication_job(self, job_entity, src_disk_meta):
        consul_api = ConsulAPI()
        jobs = consul_api.get_replication_jobs()

        for job_id, job in jobs.items():
            if job.job_name == job_entity.job_name:
                raise ReplicationException(ReplicationException.DUPLICATE_NAME, "Duplicate replication job name error.")

        manage_remote_replication = ManageRemoteReplication()

        manage_remote_replication.disk_id = job_entity.destination_disk_id
        manage_remote_replication.cluster_name = job_entity.destination_cluster_name
        job_id = consul_api.get_next_job_id()

        source_fsid = ceph_disk.get_fsid(configuration().get_cluster_name())
        job_entity.job_id = job_id
        job_entity.source_cluster_fsid = source_fsid

        src_disk_meta.replication_info["src_cluster_fsid"] = source_fsid

        mng_rep_info = ManageDiskReplicationInfo()
        src_disk_meta = mng_rep_info.set_replication_info(job_entity.destination_cluster_name, src_disk_meta)

        replication_info = src_disk_meta.replication_info

        # update source and destination disks meta.
        manage_remote_replication.update_replication_info(replication_info)
        mng_rep_info.update_replication_info(src_disk_meta, replication_info)
        system_date_time = str(datetime.datetime.now()).split('.')[0]

        # save job in consul
        consul_api.update_replication_job(job_entity)

        # Saving log in Consul :
        log_text = "{} - Job {} has been created.".format(system_date_time, job_id)
        self.log_replication_job(job_id, log_text)

        # start replication job:
        self.start_replication_job(job_entity)

    ####################################################################################################################
    # Editing a Replication Job :
    def edit_replication_job(self, job_entity, old_node):
        consul_api = ConsulAPI()

        # update job in consul
        consul_api.update_replication_job(job_entity)

        # build crontab
        self.start_node_service()

        system_date_time = str(datetime.datetime.now()).split('.')[0]
        log_text = "{} - Job {} has been updated.".format(system_date_time, job_entity.job_id)
        self.log_replication_job(job_entity.job_id, log_text)

    ####################################################################################################################
    # Getting a Replication Active Jobs :
    def get_replication_active_jobs(self):
        consul_api = ConsulAPI()
        active_jobs = consul_api.get_replication_active_jobs()
        return active_jobs

    ####################################################################################################################
    # Getting all nodes that are set as "backup" nodes :
    def get_backup_nodes(self):
        backup_nodes_list = []
        nodes_list = ManageNode().get_node_list()
        for node_info in nodes_list:
            if node_info.is_backup:
                backup_nodes_list.append(node_info.name)

        return backup_nodes_list

    ####################################################################################################################
    # Restarting the service "petasan-sync-replication-node" :
    def start_node_service(self):
        backup_nodes_list = self.get_backup_nodes()
        if len(backup_nodes_list) > 0:
            for node in backup_nodes_list:
                ManageNode().sync_replication_node(node)

    ####################################################################################################################
    # Giving disk_id of a "Local Cluster" disk , get metadata for that disk (DiskMeta Object):
    def get_src_disk_meta(self, disk_id):
        ceph_api = CephAPI()
        disk_metadata = ceph_api.get_diskmeta(disk_id)
        return disk_metadata

    ####################################################################################################################
    # Giving pool_name and disk_id , delete all snapshots of this image :
    def delete_snapshots(self, pool_name, disk_id):
        ceph_api = CephAPI()
        image_name = "image-" + disk_id
        confirm = ceph_api.delete_snapshots(pool_name, image_name)
        return confirm


