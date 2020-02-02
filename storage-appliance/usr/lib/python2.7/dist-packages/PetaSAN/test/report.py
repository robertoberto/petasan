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

import threading
from time import sleep
import math
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.cluster.network import Network
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.entity.disk_info import DiskMeta
from PetaSAN.core.lio.api import LioAPI
from PetaSAN.core.lio.network import NetworkAPI
from requests.exceptions import ConnectionError
from PetaSAN.core.common.enums import Status
import random


class Service3:
    __cluster_info = configuration().get_cluster_info()
    __node_info = configuration().get_node_info()
    __app_conf = ConfigAPI()
    __session_name = ConfigAPI().get_iscsi_service_session_name()
    __paths_local = set()
    __session = '0'
    __paths_per_disk_local = dict()
    __paths_per_session = dict()
    __total_cluster_paths = 0
    __iqn_tpgs = dict()
    __local_ips = set()
    __backstore = set()
    __current_lock_index = None
    __image_name_prefix = ""
    __cluster_info = configuration().get_cluster_info()
    __node_info = configuration().get_node_info()
    __exception_sleep_time = 0
    __acquire_warning_counter = 0
    __last_acquire_succeeded = True
    __paths_consul_unlocked_firstborn = dict()
    __paths_consul_unlocked_siblings = dict()
    __paths_consul_locked_node = dict()
    __disk_consul_stopped = set()

    is_service_running = False

    def __init__(self):
        if Service3.is_service_running:
            logger.error("The service is already running.")
            raise Exception("The service is already running.")
        Service3.is_service_running = True

    def __del__(self):
        Service3.is_service_running = False
    def __do_process(self):
        self.__paths_local = set()
        self.__paths_per_disk_local = dict()
        self.__paths_per_session = dict()
        self.__iqn_tpgs = dict()
        self.__local_ips = set()
        self.__backstore = set()
        self.__paths_consul_unlocked_firstborn = dict()
        self.__paths_consul_unlocked_siblings = dict()
        self.__paths_consul_locked_node = dict()
        self.__disk_consul_stopped = set()

        self.__read_resources_local()
        self.__read_resources_consul()

        state_change = False



    def __read_resources_local(self):
        logger.debug("Start read local resources.")
        lio_api = LioAPI()
        try:
            self.__backstore = lio_api.get_backstore_image_names()
            self.__iqn_tpgs = lio_api.get_iqns_with_enabled_tpgs()
            for iqn, tpgs in self.__iqn_tpgs.iteritems():
                disk_id = str(iqn).split(":")[1]
                for tpg_index, ips in tpgs.iteritems():
                    self.__paths_local.add("/".join([disk_id, str(tpg_index)]))
                    if ips and len(ips) > 0:
                        for ip in ips:
                            self.__local_ips.add(ip)
        except Exception as e:
            logger.error("Could not read consul resources.")
            raise e
        logger.debug("End read local resources.")

    def __read_resources_consul(self):
        logger.debug("Start read resources consul.")
        self.__paths_per_session = {}
        self.__total_cluster_paths = 0
        unlock_kvs= set()
        self.__paths_consul_locked_node= dict()
        try:
            disk_kvs = ConsulAPI().get_disk_kvs()
            for kv in disk_kvs:
                key = str(kv.Key).replace(self.__app_conf.get_consul_disks_path(), "")
                disk_id = str(key).split('/')[0]
                if disk_id in self.__disk_consul_stopped:
                    continue
                if kv.Value == "disk":
                    disk_id = str(key).split('/')[0]
                    self.__paths_per_disk_local[disk_id] = 0
                    if str(kv.Flags) == "1":
                        self.__disk_consul_stopped.add(disk_id)
                    continue
                # Count paths in the cluster.
                self.__total_cluster_paths += 1
                if hasattr(kv, "Session"):
                    disk_id = str(key).split('/')[0]
                    disks = self.__paths_consul_locked_node.get(kv.Session,dict())
                    paths = disks.get(disk_id,0)
                    disks[disk_id] = paths+1
                    self.__paths_consul_locked_node[kv.Session]=disks
                    # The count of paths for each session
                    if self.__paths_per_session.has_key(kv.Session):
                        count = self.__paths_per_session.get(kv.Session)
                        self.__paths_per_session[kv.Session] = count + 1
                    else:
                        self.__paths_per_session[kv.Session] = 1
                    if kv.Session == self.__session:
                        self.__paths_consul_locked_node.add(key)
                        disk_paths_count = self.__paths_per_disk_local.get(disk_id, 0) + 1
                        self.__paths_per_disk_local[disk_id] = disk_paths_count
                # unlocked paths
                elif not hasattr(kv, "Session"):
                    unlock_kvs.add(kv)
            # Filter unlocked paths
            for kv in unlock_kvs:
                key = str(kv.Key).replace(self.__app_conf.get_consul_disks_path(), "")
                disk_id = str(key).split('/')[0]
                if self.__paths_per_disk_local.get(disk_id,0) > 0:
                    self.__paths_consul_unlocked_siblings[key] = kv.CreateIndex
                else:
                    self.__paths_consul_unlocked_firstborn[key] = kv.CreateIndex
        except Exception as e:
            logger.error("Could not read consul resources.")
            logger.exception(e)
            raise e
        logger.debug("End read resources consul.")

    def read(self):
        self.__read_resources_consul()
        nodes = ConsulAPI().get_sessions_dict(self.__session_name)
        print "########### First born #########"
        print
        print(self.__paths_consul_unlocked_firstborn)
        # print
        # print "*********** Report *************"
        # print "Session  ;Total Paths    ;Disk   ;per disk   "
        # for sess,disks in self.__paths_consul_locked_node.iteritems():
        #     print "{}   ;{}     ".format(nodes[sess].Node,self.__paths_per_session[sess])
        #     for d,p in disks.iteritems():
        #         print "    ;         ;{}        ;{}     ".format(d,p)


while True:
    x=Service3()
    x.read()
    sleep(0.25)
    x =None


