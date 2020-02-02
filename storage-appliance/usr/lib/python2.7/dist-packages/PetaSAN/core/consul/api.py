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

from PetaSAN.core.entity.models.destination_cluster import DestinationCluster
from PetaSAN.core.entity.models.replication_active_job import ReplicationActiveJob
from PetaSAN.core.entity.models.replication_job import ReplicationJob
from flask import json
from requests import ConnectionError

from PetaSAN.core.consul.ps_consul import Consul
import sys
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.enums import ManageDiskStatus, Status
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.cluster import NodeInfo
from  PetaSAN.core.entity.kv import KV, ConsulSession
from PetaSAN.core.entity.models.replication_user import ReplicationUser
from PetaSAN.core.entity.path_assignment import PathAssignmentInfo
from PetaSAN.core.common.CustomException import ConsulException


class ConsulAPI:
    root = ConfigAPI().get_consul_disks_path()
    assignment_path = ConfigAPI().get_consul_assignment_path()
    pools = ConfigAPI().get_consul_disk_pools_path()

    # Replication
    # ===========
    replication_path = ConfigAPI().get_consul_replication_path()
    job_path = ConfigAPI().get_consul_replication_jobs_path()
    replication_log_path = ConfigAPI().get_consul_replication_logs_path()
    active_jobs_path = ConfigAPI().get_consul_replication_active_jobs_path()
    failed_jobs_path = ConfigAPI().get_consul_replication_failed_jobs_path()
    LAST_JOB_ID = 1  # initial value
    replication_destination_clusters_path = ConfigAPI().get_consul_replication_destination_clusters_path()


    def __int__(self):
        pass


    def get_new_session_ID(self, session_name, node_name, is_expire=False):
        if node_name:
            self.drop_all_node_sessions(session_name, node_name)
        consul_obj = Consul()
        if is_expire:
            session = consul_obj.session.create(name=session_name, node=node_name, behavior="delete", lock_delay=3)
        else:
            session = consul_obj.session.create(name=session_name, node=node_name)
        return session


    def add_disk_resource(self, resource, data, flag=None, current_index=0):
        consul_obj = Consul()
        status = ManageDiskStatus.error
        try:
            result = consul_obj.kv.put(self.root + resource, data, current_index, flag)
            if result:
                status = ManageDiskStatus.done
                logger.info("Successfully created key %s for new disk." % resource)
            else:
                status = ManageDiskStatus.disk_exists
                logger.error("Could not create key %s for new disk, key already exists." % resource)
        except Exception as e:
            status = ManageDiskStatus.error
            logger.error("Could not create key %s for new disk." % resource)
            logger.exception(e.message)
        return status


    def lock_disk_path(self, path, session, data, created_index):
        consul_obj = Consul()
        result = consul_obj.kv.put(path, data, None, None, str(session))
        kv = self.find_disk_path(path)
        if kv != None and int(kv.CreateIndex) == int(created_index) and result == True:
            return True
        elif kv != None and int(kv.CreateIndex) != int(created_index) and result == True:
            self.delete_disk(path)
            return False
        return False


    def release_disk_path(self, path, session, data):
        consul_obj = Consul()
        return consul_obj.kv.put(path, data, None, None, release=str(session))


    def delete_disk(self, disk_name_path, current_index=None, recurse=None):
        consul_obj = Consul()

        result = False
        try:
            result = consul_obj.kv.delete(disk_name_path, recurse, current_index)
        except Exception as e:
            return result
        return result


    def find_disk(self, disk_id):
        consul_obj = Consul()
        kv = KV()
        disk_id = str(disk_id)
        try:
            index, data = consul_obj.kv.get(str(self.root + disk_id))
            if data is not None and len(data) > 1:

                kv.load_json(json.dumps(data))
                return kv
            else:
                return None

        except Exception as e:
            logger.error("Error while trying to find disk  %s." % disk_id)
            logger.exception(e.message)
            raise e
        return None


    def is_disk_exist(self, disk_id):
        consul_obj = Consul()
        kv = KV()
        disk_id = str(disk_id)
        try:
            index, data = consul_obj.kv.get(str(self.root + disk_id))
            if data is not None and len(data) > 1:
                return True
            else:
                return False

        except Exception as e:
            logger.error("Error while checking disk exist for %s." % disk_id)
            logger.exception(e.message)
            raise e
        return False


    def find_disk_path(self, path):
        cons = Consul()
        kv = KV()
        try:
            index, data = cons.kv.get(str(path))
            if data is not None and len(data) > 1:

                kv.load_json(json.dumps(data))
                return kv
            else:
                return None

        except Exception as e:
            logger.error("Could not find disk resource.")
            logger.exception(e.message)
            return None
        return None


    def get_disk_kvs(self):
        cons = Consul()
        try:
            kvs = []
            version, data = cons.kv.get(self.root, None, True)
            index = 0
            if data:
                for i in data:
                    kv = KV()
                    kv.load_json(json.dumps(i))
                    index += 1
                    kv.sort_index = index
                    kvs.append(kv)

        except Exception as e:
            logger.error("Could not get disks kvs.")
            raise e

        return kvs


    def get_assignments(self):
        cons = Consul()
        try:
            paths = None
            version, data = cons.kv.get(self.assignment_path, None, True)
            is_root_exist = False
            if data:
                for i in data:
                    kv = KV()
                    kv.load_json(json.dumps(i))
                    path = PathAssignmentInfo()
                    if str(kv.Value) == "root":
                        is_root_exist = True
                    elif kv.Value:
                        if paths is None:
                            paths = dict()
                        path.load_json(kv.Value)
                        if hasattr(kv, "Session"):
                            path.session = kv.Session
                        paths[path.ip] = path

            if not is_root_exist:
                paths = None

        except Exception as e:
            logger.error("Could not get assignments.")
            raise e

        return paths


    def delete_assignments(self):
        consul_obj = Consul()

        result = False
        try:
            result = consul_obj.kv.delete(self.assignment_path, True)
        except Exception as e:
            return result
        return result


    def set_path_assignment(self, path_assignment_info, session):
        consul_obj = Consul()
        result = consul_obj.kv.put(ConfigAPI().get_consul_assignment_path() + path_assignment_info.ip,
                                   value=path_assignment_info.write_json(), acquire=session)
        logger.info("Lock path {} by session {}".format(path_assignment_info.ip, session))
        if not result:
            result = consul_obj.kv.put(ConfigAPI().get_consul_assignment_path() + path_assignment_info.ip,
                                       value=path_assignment_info.write_json())
        if not result:
            # self.drop_all_node_sessions(config_api.get_assignment_session_name(),configuration.get_node_name())
            logger.error("Can't create path assignment for ip {}.".format(path_assignment_info.ip))
            # raise Exception("Can't create path assignment for ip {}.".format(path_assignment_info.ip))


    def update_path_assignment(self, path_assignment_info):
        consul_obj = Consul()
        result = consul_obj.kv.put(ConfigAPI().get_consul_assignment_path() + path_assignment_info.ip,
                                   value=path_assignment_info.write_json())
        if not result:
            # self.drop_all_node_sessions(config_api.get_assignment_session_name(),configuration.get_node_name())
            logger.error("Can't update path assignment for ip {}.".format(path_assignment_info.ip))
            # raise Exception("Can't create path assignment for ip {}.".format(path_assignment_info.ip))
        return result


    def get_disk_paths(self, disk_id):
        consul_obj = Consul()
        try:
            kvs = []
            version, data = consul_obj.kv.get(self.root + disk_id, None, True)
            if data:
                for i in data:
                    kv = KV()
                    kv.load_json(json.dumps(i))
                    if kv.Value == "disk":
                        continue
                    kvs.append(kv)

        except Exception as e:
            logger.error("Could not get disk paths.")

        return kvs


    def is_path_locked_by_session(self, disk_path, session):
        consul_obj = Consul()
        Kv = None
        try:

            index, data = consul_obj.kv.get(disk_path, None, True)

            for i in data:
                kv = KV()
                kv.load_json(json.dumps(i))
                if hasattr(kv, 'Session') and kv.Session == session:
                    return True

        except Exception as e:
            raise e
        return False


    def is_path_locked(self, path):
        consul_obj = Consul()
        Kv = None
        try:

            index, data = consul_obj.kv.get("".join([self.root, path]), None, True)

            for i in data:
                kv = KV()
                kv.load_json(json.dumps(i))
                if hasattr(kv, 'Session'):
                    return True

        except Exception as e:
            return False
        return False


    def current_index(self):
        consul_obj = Consul()
        index = None
        try:
            index = consul_obj.kv.get(self.root)[0]
        except Exception as e:
            raise e

        return index


    def watch(self, curren_lock_index):
        consul_obj = Consul()
        index = None
        try:
            index = consul_obj.kv.get(self.root, curren_lock_index, False, ConfigAPI().get_consul_watch_time())[0]
            logger.debug("Current consul index is {}.".format(index))
        except KeyboardInterrupt:
            logger.error("Service end.")
            sys.exit(0)
        except Exception as e:
            logger.error("Could not start watch.")

        return index


    def get_sessions_dict(self, session_name=None, node_name=None):
        consul_obj = Consul()
        consul_sessions_list = {}
        for sess in consul_obj.session.list()[1]:
            consul_session = ConsulSession()
            consul_session.load_json(json.dumps(sess))

            if not session_name and not node_name:
                consul_sessions_list[consul_session.ID] = consul_session
                continue

            if session_name and node_name:
                if not hasattr(consul_session, 'Name'):
                    continue
                if session_name == consul_session.Name and node_name == consul_session.Node:
                    consul_sessions_list[consul_session.ID] = consul_session
                continue

            if session_name:
                if not hasattr(consul_session, 'Name'):
                    continue
                if session_name == consul_session.Name:
                    consul_sessions_list[consul_session.ID] = consul_session
                continue

            if node_name:
                if node_name == consul_session.Node:
                    consul_sessions_list[consul_session.ID] = consul_session
                continue

        return consul_sessions_list


    def drop_all_node_sessions(self, session_name, node_name):
        consul_obj = Consul()
        sessions = self.get_sessions_dict(session_name, node_name)
        for session in sessions:
            consul_obj.session.destroy(session)


    def get_leaders_startup_times(self):

        consul_obj = Consul()
        leaders_kvs = []

        index, data = consul_obj.kv.get(ConfigAPI().get_consul_leaders_path(), None, True)

        for i in data:
            kv = KV()
            kv.load_json(json.dumps(i))
            leaders_kvs.append(kv)

        return leaders_kvs


    def set_leader_startup_time(self, node_name, minutes=0):
        consul_obj = Consul()
        return consul_obj.kv.put(ConfigAPI().get_consul_leaders_path() + node_name, minutes)


    def get_node_list(self):
        consul_obj = Consul()
        index, data = consul_obj.kv.get(ConfigAPI().get_consul_nodes_path(), recurse=True)
        node_list = []
        for i in data:
            kv = KV()
            kv.load_json(json.dumps(i))
            node = NodeInfo()
            node.load_json(kv.Value)
            node_list.append(node)
        return node_list


    def get_consul_members(self):

        consul_obj = Consul()
        data = consul_obj.agent.members()
        online_members = []
        for i in data:

            member = json.loads(json.dumps(i))

            if member.has_key('Name') and member.has_key('Status'):
                # print member['Name'], member['Status']
                if member['Status'] == 1:
                    online_members.append(member['Name'])
        return online_members


    def delete_node_from_nodes_key(self, node_name):
        consul_obj = Consul()
        result = False
        try:
            result = consul_obj.kv.delete(ConfigAPI().get_consul_nodes_path() + node_name)
        except Exception as e:
            return result
        return result


    def get_node_info(self, node_name):
        try:
            consul_obj = Consul()
            index, data = consul_obj.kv.get(ConfigAPI().get_consul_nodes_path() + node_name)
            kv = KV()
            kv.load_json(json.dumps(data))
            node = NodeInfo()
            node.load_json(kv.Value)
            return node
        except Exception as e:
            return None


    # -------------------- Generic kv Functions -------------------- #
    ##################################################################


    def get_key_blocking(self, key, lock_index, timeout):
        consul_obj = Consul()
        kv = KV()
        try:
            index, data = consul_obj.kv.get(key, lock_index, False, timeout)
            if data is not None and len(data) > 1:
                kv.load_json(json.dumps(data))
                return kv
            else:
                return None

        except Exception as e:
            logger.error("Could not find key resource.")
            logger.exception(e.message)
            return None
        return None


    def get_key(self, key):
        cons = Consul()
        kv = KV()
        try:
            index, data = cons.kv.get(key)
            if data is not None and len(data) > 1:
                kv.load_json(json.dumps(data))
                return kv
            else:
                return None

        except Exception as e:
            logger.error("Could not find key resource.")
            logger.exception(e.message)
            return None
        return None


    def current_key_index(self, key):
        consul_obj = Consul()
        index = None
        try:
            index = consul_obj.kv.get(key)[0]
        except Exception as e:
            logger.error("Could not get current index from consul.")

        return index


    def watch_key(self, key, lock_index, timeout):
        consul_obj = Consul()
        index = None
        try:
            index = consul_obj.kv.get(key, lock_index, False, timeout)[0]

        except KeyboardInterrupt:
            logger.info("Service end.")
            sys.exit(0)
        except Exception as e:
            logger.error("Could not start watch.")

        return index


    def lock_key(self, key, session, data):
        consul_obj = Consul()
        return consul_obj.kv.put(key, data, None, None, acquire=str(session))


    def unlock_key(self, key, session, data):
        consul_obj = Consul()
        return consul_obj.kv.put(key, data, None, None, release=str(session))


    def is_key_locked_by_session(self, key, session):
        consul_obj = Consul()
        Kv = None
        try:

            index, data = consul_obj.kv.get(key, None, True)

            for i in data:
                kv = KV()
                kv.load_json(json.dumps(i))
                if hasattr(kv, 'Session') and kv.Session == session:
                    return True

        except Exception as e:
            raise e
        return False


    def is_key_locked(self, key):
        consul_obj = Consul()
        Kv = None
        try:

            index, data = consul_obj.kv.get(key, None, True)

            for i in data:
                kv = KV()
                kv.load_json(json.dumps(i))
                if hasattr(kv, 'Session'):
                    return True

        except Exception as e:
            return False
        return False


    def get_running_disks(self):
        cons = Consul()
        ids = []
        try:
            index, data = cons.kv.get(self.root, None, True)
            if data:
                for i in data:
                    kv = KV()
                    kv.load_json(json.dumps(i))
                    if kv.Value == 'disk':
                        disk_id = kv.Key.replace(self.root, '')
                        ids.append(disk_id)
        except Exception as e:
            logger.error('Consul Could not get running disks.')
            raise ConsulException(ConsulException.GENERAL_EXCEPTION, 'GeneralConsulError')

        return ids


    # -------------------- Disk Pools -------------------- #
    ########################################################


    def add_disk_pool(self, disk_id, pool):
        consul_obj = Consul()
        index = 0
        kv = self._get_disk_pool_kv(disk_id)
        if kv:
            if kv.Value == pool:
                return
            else:
                index = kv.ModifyIndex
        try:
            consul_obj.kv.put(self.pools + disk_id, pool, index)
        except Exception as e:
            logger.error('Consul Error adding pool {} for disk {} .'.format(pool, disk_id))
            logger.exception(e.message)
            raise ConsulException(ConsulException.GENERAL_EXCEPTION, 'GeneralConsulError')


    def get_disk_pool(self, disk_id):
        kv = self._get_disk_pool_kv(disk_id)
        if not kv:
            return None
        return kv.Value


    def _get_disk_pool_kv(self, disk_id):
        consul_obj = Consul()
        try:
            kv = KV()
            index, data = consul_obj.kv.get(self.pools + disk_id)
            if data is not None and len(data) > 1:
                kv.load_json(json.dumps(data))
                return kv
            else:
                return None

        except Exception as e:
            logger.error('Consul Error reading pool for disk  %s.' % disk_id)
            logger.exception(e.message)
            raise ConsulException(ConsulException.GENERAL_EXCEPTION, 'GeneralConsulError')
        return None


    def get_disk_pools(self):
        disk_pools = {}
        kvs = self._get_disk_pools_kvs()
        for kv in kvs:
            disk_id = kv.Key.replace(self.pools, '')
            disk_pools[disk_id] = kv.Value

        return disk_pools


    def _get_disk_pools_kvs(self):
        cons = Consul()
        kvs = []
        try:
            index, data = cons.kv.get(self.pools, None, True)
            if data:
                for i in data:
                    kv = KV()
                    kv.load_json(json.dumps(i))
                    kvs.append(kv)
        except Exception as e:
            logger.error('Consul Could not get disk pools kvs.')
            raise ConsulException(ConsulException.GENERAL_EXCEPTION, 'GeneralConsulError')

        return kvs


    # -------------------- Replication -------------------- #
    #########################################################

    def update_replication_job(self, job_entity):
        consul_obj = Consul()
        key = self.job_path + job_entity.job_id
        result = consul_obj.kv.put(key, value=job_entity.write_json())

        if not result:
            logger.error("Consul Error : Can't add replication job {}.".format(job_entity.job_name))
        return result


    def update_replication_user(self, user_entity):
        consul = Consul()
        key = ConfigAPI().get_consul_replication_users_path() + user_entity.user_name
        result = consul.kv.put(key, value=user_entity.write_json())
        if not result:
            logger.error("Consul Error : Can't add replication user {}.".format(user_entity.user_name))

        return result


    def update_replication_active_job(self, active_job_entity):
        try:
            consul_obj = Consul()
            active_job_id = active_job_entity.job_id.split('-')
            rep_job_id = active_job_id[0]
            key = self.active_jobs_path + rep_job_id
            result = consul_obj.kv.put(key, value=active_job_entity.write_json())

            if not result:
                logger.error("Consul Error : Can't add active replication job {}.".format(active_job_entity.job_name))
        except Exception as e:
            logger.error('Consul Could not get Replication users.')
            raise ConsulException(ConsulException.GENERAL_EXCEPTION, 'GeneralConsulError')

        return result


    def add_replication_failed_job(self, job_entity):
        consul_obj = Consul()
        key = self.failed_jobs_path + job_entity.job_id
        result = consul_obj.kv.put(key, value=job_entity.write_json())

        if not result:
            logger.error("Consul Error : Can't add replication failed job {}.".format(job_entity.job_name))
        return result


    def get_replication_jobs(self):
        try:
            consul_obj = Consul()
            jobs_dict = {}

            index, data = consul_obj.kv.get(ConfigAPI().get_consul_replication_jobs_path(), recurse=True)

            if data and len(data) > 0 :
                for i in data:
                    kv = KV()
                    kv.load_json(json.dumps(i))

                    rep_job = ReplicationJob()
                    rep_job.load_json(kv.Value)
                    jobs_dict[rep_job.job_id] = rep_job

            return jobs_dict

        except Exception as e:
            logger.error('Consul Could not get Replication Jobs kvs.')
            raise ConsulException(ConsulException.GENERAL_EXCEPTION, 'GeneralConsulError')



    def get_replication_users(self):
        try:
            consul = Consul()
            users_info = {}
            index, data = consul.kv.get(ConfigAPI().get_consul_replication_users_path(), recurse=True)
            if data and len(data) > 0:
                for user in data:
                    kv = KV()
                    kv.load_json(json.dumps(user))
                    user_info = ReplicationUser()
                    user_info.load_json(kv.Value)
                    users_info[user_info.user_name] = user_info
            return users_info

        except Exception as e:
            logger.error(e)
            raise ConsulException(ConsulException.GENERAL_EXCEPTION, 'GeneralConsulError')


    def get_replication_active_job(self, job_id):
        try:
            consul = Consul()
            index, data = consul.kv.get(ConfigAPI().get_consul_replication_active_jobs_path() + job_id)
            if data:
                kv = KV()
                kv.load_json(json.dumps(data))

                rep_job = ReplicationActiveJob()
                rep_job.load_json(kv.Value)

                return rep_job

            return None

        except Exception as e:
            return None


    def get_replication_job(self, job_id):
        try:
            consul_obj = Consul()
            index, data = consul_obj.kv.get(ConfigAPI().get_consul_replication_jobs_path() + job_id)

            if data and len(data) > 0:
                kv = KV()
                kv.load_json(json.dumps(data))

                rep_job = ReplicationJob()
                rep_job.load_json(kv.Value)

                return rep_job

            return None

        except Exception as e:
            return None


    def get_replication_user(self, user_name):
        try:
            consul = Consul()
            index, data = consul.kv.get(ConfigAPI().get_consul_replication_users_path() + user_name)
            user_info = ReplicationUser()
            if data and len(data) > 0:
                kv = KV()
                kv.load_json(json.dumps(data))
                user_info.load_json(kv.Value)

            return user_info

        except Exception as e:
            logger.error(e)
            raise ConsulException(ConsulException.GENERAL_EXCEPTION, 'GeneralConsulError')


    def get_replication_active_jobs(self):
        try:
            consul_obj = Consul()
            active_jobs = {}

            index, data = consul_obj.kv.get(ConfigAPI().get_consul_replication_active_jobs_path(), recurse=True)

            if data and len(data) > 0 :
                for i in data:
                    kv = KV()
                    kv.load_json(json.dumps(i))

                    active_job = ReplicationActiveJob()
                    active_job.load_json(kv.Value)
                    active_jobs[active_job.job_id] = active_job

            return active_jobs

        except Exception as e:
            return None


    def get_replication_failed_jobs(self):
        try:
            consul_obj = Consul()
            failed_jobs = {}

            index, data = consul_obj.kv.get(ConfigAPI().get_consul_replication_failed_jobs_path(), recurse=True)

            if data and len(data) > 0 :
                for i in data:
                    kv = KV()
                    kv.load_json(json.dumps(i))

                    rep_job = ReplicationJob()
                    rep_job.load_json(kv.Value)
                    failed_jobs[rep_job.job_id] = rep_job

            return failed_jobs

        except Exception as e:
                    return None


    def delete_failed_job(self, job_id, recurse=True):
        consul = Consul()
        result = False

        try:
            result = consul.kv.delete(ConfigAPI().get_consul_replication_failed_jobs_path() + job_id, recurse)

        except Exception as e:
            return result

        return result


    def delete_replication_job(self, job_entity, recurse=True):
        consul_obj = Consul()
        result = False

        try:
            result = consul_obj.kv.delete(ConfigAPI().get_consul_replication_jobs_path() + job_entity.job_id, recurse)

        except Exception as e:
            return result

        return result


    def delete_replication_user(self, user_name, recurse=True):
        consul = Consul()
        result = False
        try:
            result = consul.kv.delete(ConfigAPI().get_consul_replication_users_path() + user_name, recurse)

        except Exception as e:
            logger.error(e)
            raise ConsulException(ConsulException.GENERAL_EXCEPTION, 'GeneralConsulError')
        return result


    def delete_active_job(self, job_id, recurse=True):
        consul = Consul()
        result = False
        try:
            result = consul.kv.delete(ConfigAPI().get_consul_replication_active_jobs_path() + job_id , recurse)

        except Exception as e:
            logger.error(e)

        return result


    def get_replication_job_log(self, job_id):
        try:
            ls = []
            consul_obj = Consul()
            index, data = consul_obj.kv.get(ConfigAPI().get_consul_replication_logs_path() + job_id)

            if data:
                kv = KV()
                kv.load_json(json.dumps(data))
                ls = kv.Value
            return ls

        except Exception as e:
            return None


    def log_replication_job(self, job_id, list_of_txt):
        consul_obj = Consul()
        key = self.replication_log_path + job_id
        result = consul_obj.kv.put(key, value=list_of_txt)

        if not result:
            logger.error("Consul Error : Can't add replication job {} log.".format(job_id))
        return result


    def delete_replication_log(self, job_entity, recurse=True):
        consul_obj = Consul()
        result = False

        try:
            result = consul_obj.kv.delete(ConfigAPI().get_consul_replication_logs_path() + job_entity.job_id, recurse)

        except Exception as e:
            return result

        return result


    def get_next_job_id(self):
        try:
            consul_obj = Consul()
            kv = KV()
            index, data = consul_obj.kv.get(ConfigAPI().get_consul_replication_last_job_id_path())

            if data is None:
                last_job_id = self.LAST_JOB_ID
                next_job_id = last_job_id

            else:
                kv.load_json(json.dumps(data))
                last_job_id = int(kv.Value)
                next_job_id = last_job_id + 1

            next_job_id_str = "{:05d}".format(next_job_id)

            key = ConfigAPI().get_consul_replication_last_job_id_path()
            value = str(next_job_id)
            result = consul_obj.kv.put(key, value)

            return next_job_id_str

        except Exception as e:
            print(e.message)
            return None

    def update_replication_destination_cluster(self, dest_cluster_entity):
        consul_obj = Consul()
        key = self.replication_destination_clusters_path + dest_cluster_entity.cluster_name
        result = consul_obj.kv.put(key, value=dest_cluster_entity.write_json())

        if not result:
            logger.error("Consul Error : Can't add destination cluster {}.".format(dest_cluster_entity.cluster_name))
        return result


    def delete_replication_destination_cluster(self, dest_cluster_entity, recurse=True):
        consul_obj = Consul()
        result = False

        try:
            result = consul_obj.kv.delete(self.replication_destination_clusters_path + dest_cluster_entity.cluster_name, recurse)

        except Exception as e:
            return result

        return result

    def get_replication_destination_cluster(self, dest_cluster_name):
        try:
            consul_obj = Consul()
            index, data = consul_obj.kv.get(self.replication_destination_clusters_path + dest_cluster_name)

            if data:
                kv = KV()
                kv.load_json(json.dumps(data))

                dest_cluster = DestinationCluster()
                dest_cluster.load_json(kv.Value)

                return dest_cluster

            return None

        except Exception as e:
            return None

    def get_replication_destination_clusters(self):
        try:
            consul_obj = Consul()
            dest_clusters = {}

            index, data = consul_obj.kv.get(self.replication_destination_clusters_path, recurse=True)

            if data and len(data) > 0 :
                for i in data:
                    kv = KV()
                    kv.load_json(json.dumps(i))
                    dest_cluster = DestinationCluster()
                    dest_cluster.load_json(kv.Value)
                    dest_clusters[dest_cluster.cluster_name] = dest_cluster

            return dest_clusters

        except Exception as e:
            logger.error('Consul Could not get Destination Clusters kvs.')
            raise ConsulException(ConsulException.GENERAL_EXCEPTION, 'GeneralConsulError')

