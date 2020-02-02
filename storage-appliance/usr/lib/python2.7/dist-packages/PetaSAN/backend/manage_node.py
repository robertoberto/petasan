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
import re

from PetaSAN.backend.file_sync_manager import FileSyncManager
from PetaSAN.core.ceph import ceph_osd
from PetaSAN.core.ceph.ceph_disk import get_journal_size
from PetaSAN.core.common.enums import NodeStatus, OsdStatus, DeleteNodeStatus
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.entity.ph_disk import DiskInfo
from PetaSAN.core.ssh.ssh import ssh
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.CustomException import DiskException
from PetaSAN.core.ceph import ceph_disk_lib


class ManageNode:
    def __init__(self):
        pass

    ####################################################################################################################
    # Get all PetaSAN nodes with up or down status.
    def get_node_list(self):
        consul_api = ConsulAPI()
        # Get all PetaSAN nodes[management or storage].
        node_list = consul_api.get_node_list()
        # Get online nodes from consul.
        consul_members = consul_api.get_consul_members()
        petasan_node_list = []
        for i in node_list:
            if i.name in consul_members:
                i.status = NodeStatus.up
            else:
                i.status = NodeStatus.down
            petasan_node_list.append(i)

        return petasan_node_list

    ####################################################################################################################
    def get_disk_list(self, node_name, pid):
        """
        DOCSTRING : this function is called to execute ssh command to get all disks from other nodes.
        Args : node_name (string), pid (integer)
        Returns : all disks on node_name
        """
        ssh_obj = ssh()
        cmd = "python {} {}  {}".format(ConfigAPI().get_admin_manage_node_script(), "disk-list -pid", pid)
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        # stdout,stderr =exec_command(cmd)
        if stderr and str(stderr).lower().find("Warning".lower()) == -1:
            logger.error(stderr)
            return None
        else:
            data = json.loads(str(stdout))
            disk_list = []
            for i in data:
                disk_info = DiskInfo()
                disk_info.load_json(json.dumps(i))
                disk_list.append(disk_info)
            return disk_list

    ####################################################################################################################
    def get_disks_health(self, node_name):
        ssh_obj = ssh()
        disks_health = {}
        cmd = "python {} {}".format(ConfigAPI().get_admin_manage_node_script(), "disk-health")
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        # stdout,stderr =exec_command(cmd)
        if stderr and str(stderr).lower().find("Warning".lower()) == -1:
            logger.error(stderr)
            return disks_health
        else:

            disks_health = json.loads(str(stdout))
            return disks_health

    ####################################################################################################################
    def delete_osd(self, node_name, disk_name, osd_id):
        ssh_obj = ssh()
        cmd = "python {} -id {}  -disk_name {}".format(ConfigAPI().get_admin_delete_osd_job_script(), osd_id, disk_name)
        # stdout,stderr =exec_command(cmd)
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        logger.info("Start delete osd job {} ".format(stdout))
        return stdout

    ####################################################################################################################
    def add_osd(self, node_name, disk_name, journal=None, cache=None, cache_type="disabled"):
        """
        :param node_name:
        :param disk_name:
        :param journal:
        :param cache:
        :param cache_type:
        :return: it will return pid number, so pid will use to track the error message if occurred ,
        if it returns -1 , this means : core_manage_node_add_osd_err
        """
        # Journal value will be :
        #   -   None : if no journal exist ,
        #   -   disk_name : if user selected a journal or
        #   -   auto : if user did not select journal

        ssh_obj = ssh()
        cmd = ""
        # ---------------------------------------------------------------------- #
        if journal:
            if journal != "auto":
                if not self.is_journal_space_avail(node_name, str(journal).lower()):
                    raise DiskException(DiskException.JOURNAL_NO_SPACE,
                                        'There is no disk space for a new OSD with journal.')

            if not self.has_valid_journal(node_name):
                raise DiskException(DiskException.JOURNALS_NO_SPACE,
                                    'There is no disk space for a new OSD with all existing journals.')
        # ---------------------------------------------------------------------- #
        if cache:
            if cache != 'auto':
                if not self.is_cache_partition_avail(node_name, str(cache).lower()):
                    raise DiskException(DiskException.CACHE_NO_SPACE,
                                        'There is no disk space for a new OSD with cache.')

            if not self.has_valid_cache(node_name):
                raise DiskException(DiskException.CACHE_NO_SPACE,
                                    'There is no disk space for a new OSD with all existing caches.')
        # ---------------------------------------------------------------------- #

        # Adding OSD with Journal & Cache :
        # =================================
        if journal and cache and cache_type != "disabled":
            cmd = "python {} -disk_name {} -journal {} -cache {} -cache_type {}".format(
                ConfigAPI().get_admin_add_osd_job_script(), disk_name, str(journal).lower(),
                str(cache).lower(), str(cache_type))

        # Adding OSD with Journal :
        # =========================
        elif journal:
            cmd = "python {} -disk_name {} -journal {}".format(
                ConfigAPI().get_admin_add_osd_job_script(), disk_name, str(journal).lower())

        # Adding OSD with Cache :
        # =======================
        elif cache and cache_type != "disabled":
            cmd = "python {} -disk_name {} -cache {} -cache_type {}".format(
                ConfigAPI().get_admin_add_osd_job_script(), disk_name, str(cache).lower(), str(cache_type))

        # Adding OSD :
        # ============
        elif journal is None and cache is None:
            cmd = "python {} -disk_name {}".format(ConfigAPI().get_admin_add_osd_job_script(), disk_name)

        # stdout, stderr = exec_command(cmd)
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        logger.info("Start add osd job {} ".format(stdout))

        return stdout

    ####################################################################################################################
    def get_node_info(self, node_name):
        return ConsulAPI().get_node_info(node_name)

    ####################################################################################################################
    def get_node_log(self, node_name):
        ssh_obj = ssh()
        cmd = "python {} {}  ".format(ConfigAPI().get_admin_manage_node_script(), "node-log")
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        # stdout,stderr =exec_command(cmd)
        return stdout

    ####################################################################################################################
    def delete_node(self, node_name):
        osd_dict = ceph_osd.ceph_osd_tree(node_name)
        if osd_dict and OsdStatus.up in osd_dict.values():
            return DeleteNodeStatus.not_allow

        if osd_dict:
            logger.info("Remove all osds of node {} from ceph crush map.".format(node_name))
            for i in osd_dict.keys():
                ceph_osd.delete_osd_from_crush_map(i)
        logger.info("Remove node {} from ceph crush map.".format(node_name))
        ceph_osd.delete_node_from_crush_map(node_name)
        if ConsulAPI().delete_node_from_nodes_key(node_name):
            logger.info("Remove node {} from consul 'Nodes' key.".format(node_name))

            if self._remove_node_from_hosts(node_name):
                if FileSyncManager().commit_file(self.path):
                    return DeleteNodeStatus.done

        logger.Error("Failed to remove node {}.".format(node_name))
        return DeleteNodeStatus.error

    path = "/etc/hosts"

    ####################################################################################################################
    def _remove_node_from_hosts(self, node_name):
        try:
            with open(self.path, 'r+') as f:
                lines = f.readlines()
                f.seek(0)
                f.truncate()
                for line in lines:
                    host_line = str(line).replace("\t", " ").replace("\n", " ").strip()
                    if host_line != "":
                        values = host_line.split(" ")
                        ip = values[0]
                        host_name = values[len(values) - 1]
                        if host_name != node_name:
                            f.write("{ip_addr}   {host}\n".format(ip_addr=ip, host=host_name))
            return True
        except Exception as e:
            logger.exception(e.message)
            logger.error("Could not read/write hosts file.")
            return False

    ####################################################################################################################
    def update_node_role(self, node_name, is_storage=-1, is_iscsi=-1, is_backup=-1):
        ssh_obj = ssh()
        'update-role -is_iscsi 1 -is_storage 1'
        cmd = "python {} update-role -is_iscsi {} -is_storage {} -is_backup {}".format(
            ConfigAPI().get_admin_manage_node_script(),
            is_iscsi, is_storage, is_backup)
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        # stdout,stderr =exec_command(cmd)
        if stderr:
            return None
        else:
            if str(stdout) == "1" or stdout == None:
                return
            elif str(stdout) == "-1":
                raise Exception('Error update node roles.')

    ####################################################################################################################
    def read_file(self, file_path):
        f = open(file_path)
        while True:
            data = f.read(1024)
            if not data:
                f.close()
                break
            yield data

    ####################################################################################################################
    def add_journal(self, node_name, disk_name):
        ssh_obj = ssh()
        cmd = "python {} -disk_name {}".format(ConfigAPI().get_admin_add_journal_job_script(), disk_name)
        # stdout,stderr =exec_command(cmd)# for test local
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        logger.info("Start add journal job {} ".format(stdout))
        return stdout

    ####################################################################################################################
    def delete_journal(self, node_name, disk_name):
        ssh_obj = ssh()
        cmd = "python {} -disk_name {}".format(ConfigAPI().get_admin_delete_journal_job_script(), disk_name)
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        logger.info("Start delete journal job {} ".format(stdout))
        return stdout

    ####################################################################################################################
    def is_journal_space_avail(self, node_name, disk_name):
        ssh_obj = ssh()
        config = configuration()
        cluster_name = config.get_cluster_name()
        cmd = "python {} {} {}".format(ConfigAPI().get_admin_manage_node_script(), "disk-avail-space -disk_name",
                                       disk_name)
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        free_disk_space = float(re.findall(r'-?\d+\.?\d*', stdout)[0])
        bluestore_block_db_size = get_journal_size()
        if free_disk_space > bluestore_block_db_size:
            return True
        return False

    ####################################################################################################################
    def has_valid_journal(self, node_name):
        ssh_obj = ssh()
        cmd = "python {} {}".format(ConfigAPI().get_admin_manage_node_script(), "valid-journal")
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        if 'None' in stdout:
            return False
        return True

    ####################################################################################################################
    def sync_replication_node(self, node_name):
        ssh_obj = ssh()
        cmd = 'systemctl restart petasan-sync-replication-node'
        return ssh_obj.call_command(node_name, cmd)

    ####################################################################################################################
    def add_cache(self, node_name, disk_name, partitions):
        ssh_obj = ssh()
        cmd = "python {} -disk_name {} -partitions {}".format(ConfigAPI().get_admin_add_cache_job_script(), disk_name, partitions)

        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        logger.info("Start add cache job {}".format(stdout))
        return stdout

    ####################################################################################################################
    def delete_cache(self, node_name, disk_name):
        ssh_obj = ssh()
        cmd = "python {} -disk_name {}".format(ConfigAPI().get_admin_delete_cache_job_script(), disk_name)
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)
        logger.info("Start delete cache job {} ".format(stdout))
        return stdout

    ####################################################################################################################
    def is_cache_partition_avail(self, node_name, disk_name):
        ssh_obj = ssh()
        config = configuration()
        cluster_name = config.get_cluster_name()

        cmd = "python {} {} {}".format(ConfigAPI().get_admin_manage_node_script(), "cache-partition-avail -disk_name",
                                       disk_name)
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)

        if 'True' in stdout:
            return True

        return False

    ####################################################################################################################
    def has_valid_cache(self, node_name):
        ssh_obj = ssh()
        config = configuration()
        cluster_name = config.get_cluster_name()

        cmd = "python {} {}".format(ConfigAPI().get_admin_manage_node_script(), "valid-cache")
        stdout, stderr = ssh_obj.exec_command(node_name, cmd)

        if 'None' in stdout:
            return False
        else:
            return True

    ####################################################################################################################
