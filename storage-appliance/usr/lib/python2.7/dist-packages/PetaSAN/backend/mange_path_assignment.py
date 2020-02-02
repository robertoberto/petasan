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

from PetaSAN.core.common.cmd import call_cmd
from PetaSAN.core.ssh.ssh import ssh
from time import sleep
from PetaSAN.core.cluster.network import Network
from PetaSAN.core.lio.network import NetworkAPI
from PetaSAN.core.lio.api import LioAPI
from PetaSAN.core.common.enums import ReassignPathStatus
from PetaSAN.core.common.log import logger
from PetaSAN.core.cluster.configuration import configuration
from flask import json
from PetaSAN.core.entity.disk_info import Path
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.entity.path_assignment import AssignmentStats, PathAssignmentInfo
from PetaSAN.core.path_assignment.base import AssignmentContext

auto_plugins = ['PetaSAN.core.path_assignment.plugins.average_paths']


class MangePathAssignment(object):
    def __init__(self):
        self.__app_conf = ConfigAPI()
        self.__context = AssignmentContext()
        self.__session_dict = ConsulAPI().get_sessions_dict(ConfigAPI().get_iscsi_service_session_name())
        self.__node_session_dict = dict()
        pass

    def get_assignments_stats(self):
        return self._filter_assignments_stats()

    def search_by_disk_name(self, disk_name):
        return self._filter_assignments_stats(filter_type=1, filter_text=disk_name)

    def search_by_ip(self, ip):
        return self._filter_assignments_stats(filter_type=2, filter_text=ip)

    def _filter_assignments_stats(self, filter_type=0, filter_text=None, set_session=False):

        __disk_consul_stopped = set()
        running_paths = dict()
        ceph_api = CephAPI()
        consul_api = ConsulAPI()
        disk_kvs = consul_api.get_disk_kvs()

        # Step 1 get all running paths.
        for consul_kv_obj in disk_kvs:
            path_key = str(consul_kv_obj.Key).replace(self.__app_conf.get_consul_disks_path(), "")
            disk_id = str(path_key).split('/')[0]
            if disk_id in __disk_consul_stopped:
                continue
            if consul_kv_obj.Value == "disk":
                disk_id = str(path_key).split('/')[0]

                # Step 2 avoid stopping disks
                if str(consul_kv_obj.Flags) == "1":
                    __disk_consul_stopped.add(disk_id)
                continue

            running_paths[path_key] = consul_kv_obj

        if len(running_paths) == 0:
            return AssignmentStats()

        # Step 3 get all images metadata
        images = ceph_api.get_disks_meta()

        assignment_stats = AssignmentStats()

        # Step 4 get current reassignments
        current_running_assignments = self.get_current_reassignment()
        if current_running_assignments is not None:
            assignment_stats.is_reassign_busy = True
            filter_type = 0  # we will stop any filter and get all data if here is running reassignment

        # Step 5 fill paths assignment info
        for path_key, consul_kv_obj in running_paths.iteritems():
            disk_id = str(path_key).split('/')[0]
            disk = next((img for img in images if img.id == disk_id), None)
            if disk is None:
                continue
            disk_path = Path()

            path_index = int(str(path_key).split(disk_id + "/")[1])
            path_str = disk.paths[path_index - 1]
            disk_path.load_json(json.dumps(path_str))

            path_assignment_info = PathAssignmentInfo()
            path_assignment_info.interface = disk_path.eth
            if disk_path.vlan_id:
                path_assignment_info.interface = disk_path.eth + "." + disk_path.vlan_id
            path_assignment_info.ip = disk_path.ip
            path_assignment_info.disk_name = disk.disk_name
            path_assignment_info.disk_id = disk_id
            path_assignment_info.index = path_index
            current_path = None
            if current_running_assignments is not None:
                current_path = current_running_assignments.get(disk_path.ip)
            if hasattr(consul_kv_obj, "Session") and self.__session_dict.has_key(consul_kv_obj.Session):
                # Fill status and node name for started paths
                path_assignment_info.node = self.__session_dict.get(consul_kv_obj.Session).Node

                if current_running_assignments is not None:

                    if current_path is not None and current_path.status != -1:
                        path_assignment_info.status = current_path.status
                        path_assignment_info.target_node = current_path.target_node
                        if set_session:
                            # session refers to the node that lock this path assignment,This property helps to know the
                            # status of path and the node will handle this path
                            path_assignment_info.session = current_path.session
            elif current_path:
                path_assignment_info.node = current_path.node
                path_assignment_info.target_node = current_path.target_node
                path_assignment_info.status = current_path.status
                if set_session:
                    path_assignment_info.session = current_path.session

            # Step 6 search or get all
            if filter_type == 1 and filter_text is not None and len(str(filter_text).strip()) > 0:  # by disk name
                if filter_text.strip().lower() in path_assignment_info.disk_name.lower():
                    assignment_stats.paths.append(path_assignment_info)
            elif filter_type == 2 and filter_text is not None and len(str(filter_text).strip()) > 0:  # by ip
                if filter_text.strip() == path_assignment_info.ip.strip():
                    assignment_stats.paths.append(path_assignment_info)
                    break
            else:
                assignment_stats.paths.append(path_assignment_info)

            # Step 7 set all online nodes
        assignment_stats.nodes = self._get_nodes()

        return assignment_stats

    def get_current_reassignment(self):
        paths = ConsulAPI().get_assignments()
        if paths is not None:
            for ip, path_assignment_info in paths.iteritems():
                if not hasattr(path_assignment_info, "session"):
                    logger.info("Path {} not locked by node.".format(path_assignment_info.ip))
                if not hasattr(path_assignment_info, "session") and path_assignment_info.status not in [
                    ReassignPathStatus.succeeded, ReassignPathStatus.failed]:
                    path_assignment_info.status = ReassignPathStatus.failed
        return paths

    def set_new_assignments(self, paths_assignment_info):
        logger.info("Set new assignment.")
        if self.get_current_reassignment() is not None:
            raise Exception("There is already running assignment.")

        config_api = ConfigAPI()
        consul_api = ConsulAPI()
        logger.info("Delete old assignments.")
        consul_api.delete_assignments()
        session = consul_api.get_new_session_ID(config_api.get_assignment_session_name(),
                                                configuration().get_node_name(), True)
        if consul_api.lock_key(config_api.get_consul_assignment_path(), session, "root"):
            logger.info("Lock assignment root.")
            for path_assignment_info in paths_assignment_info:
                path_assignment_info.status = ReassignPathStatus.pending
                consul_api.set_path_assignment(path_assignment_info,
                                               self._get_node_session(path_assignment_info.target_node))
                logger.info("New assignment for {} ,disk {}, from node {}  and to node {} with status {}".format(
                    path_assignment_info.ip, path_assignment_info.disk_id, path_assignment_info.node,
                    path_assignment_info.target_node, path_assignment_info.status
                ))
        else:
            logger.error("Can't lock paths assignment key.")
            raise Exception("Can't lock paths assignment key.")

    def run(self):

        cmd = "python {} server &".format(ConfigAPI().get_assignment_script_path())
        call_cmd(cmd)

    def _get_nodes(self):
        consul_api = ConsulAPI()
        # Get all PetaSAN nodes[management or storage].
        node_list = consul_api.get_node_list()
        # Get online nodes from consul.
        consul_members = consul_api.get_consul_members()
        petasan_node_list = []
        for i in node_list:
            if not i.is_iscsi:
                continue
            if i.name in consul_members:
                petasan_node_list.append(i.name)

        return petasan_node_list

    def remove_assignment(self):
        consul_api = ConsulAPI()
        if consul_api.get_assignments() is not None:
            consul_api.delete_assignments()

    def auto(self, type=1):
        logger.info("User start auto reassignment paths.")
        assignments_stats = self.get_assignments_stats()
        if assignments_stats.is_reassign_busy:
            logger.error("There is already reassignment running.")
            raise Exception("There is already reassignment running.")

        ConsulAPI().drop_all_node_sessions(self.__app_conf.get_consul_assignment_path(),
                                           configuration().get_node_name())
        sleep(3)

        assignments_stats.paths = [path for path in assignments_stats.paths if
                                   len(path.node.strip()) > 0 and path.status == -1]
        self.__context.paths = assignments_stats.paths
        self.__context.nodes = assignments_stats.nodes
        for plugin in self._get_new_plugins_instances(auto_plugins):
            if plugin.is_enable() and plugin.get_plugin_id() == type:
                paths_assignments = plugin.get_new_assignments()
                if len(paths_assignments) == 0:
                    logger.info("There is no node under average.")
                    return
                self.set_new_assignments(paths_assignments)
                break
        self.run()

    def manual(self, paths_assignment_info, assign_to="auto"):

        assignments_stats = self.get_assignments_stats()
        if assignments_stats.is_reassign_busy:
            logger.error("There is already reassignment running.")
            raise Exception("There is already reassignment running.")
        ConsulAPI().drop_all_node_sessions(self.__app_conf.get_consul_assignment_path(),
                                           configuration().get_node_name())
        sleep(3)  # Wait to be sure the session dropped
        if assign_to == "auto":

            logger.info("User start auto reassignment paths for selected paths.")
            assignments_stats.paths = [path for path in assignments_stats.paths if
                                       len(path.node.strip()) > 0 and path.status == -1]
            self.__context.paths = assignments_stats.paths
            self.__context.nodes = assignments_stats.nodes
            self.__context.user_input_paths = paths_assignment_info
            for plugin in self._get_new_plugins_instances(auto_plugins):
                if plugin.is_enable() and plugin.get_plugin_id() == 1:
                    paths_assignments = plugin.get_new_assignments()
                    self.set_new_assignments(paths_assignments)
                    logger.info("User start auto reassignment paths for selected paths.")
                    self.run()
                    break
            pass
        else:

            for path_assignment_info in paths_assignment_info:
                path_assignment_info.target_node = assign_to
                path_assignment_info.status = ReassignPathStatus.pending
            logger.info("User start manual reassignment paths for selected paths.")
            self.set_new_assignments(paths_assignment_info)

            self.run()

    def process(self):
        logger.info("Start process reassignments paths.")
        max_retry = 100
        current_reassignments = self.get_current_reassignment()
        config = configuration()
        assignment_script_path = ConfigAPI().get_assignment_script_path()
        if current_reassignments is None:
            return
        for ip, path_assignment_info in current_reassignments.iteritems():
            logger.info("process path {} and its status is {}".format(ip, path_assignment_info.status))
            if path_assignment_info.status == ReassignPathStatus.pending:
                logger.info(
                    "Move action,try clean disk {} path {} remotely on node {}.".format(path_assignment_info.disk_name,
                                                                                        path_assignment_info.disk_id,
                                                                                        path_assignment_info.node))

                status = False
                try:

                    cmd = "python {} path_host -ip {} -disk_id {}".format(assignment_script_path,
                                                                          path_assignment_info.ip
                                                                          , path_assignment_info.disk_id)
                    out, err = ssh().exec_command(path_assignment_info.node, cmd)
                    logger.info(cmd)
                    # self.clean_source_node(path_assignment_info.ip,path_assignment_info.disk_id)
                except Exception as ex:
                    logger.exception(ex.message)
                    out = ""

                if str(out).strip() == "0":
                    logger.info("Move action passed")
                    status = True

                current_path_assignment_info = None
                if status:
                    for i in xrange(0, max_retry):
                        logger.debug("Wait to update status of path {}.".format(path_assignment_info.ip))
                        sleep(0.25)
                        reassignments = self.get_current_reassignment()
                        if reassignments:
                            current_path_assignment_info = reassignments.get(path_assignment_info.ip)
                            if current_path_assignment_info and current_path_assignment_info.status == ReassignPathStatus.moving:
                                continue
                            else:
                                logger.info(
                                    "Process completed for path {} with status {}.".format(
                                        current_path_assignment_info.ip,
                                        current_path_assignment_info.status))
                                break
                    if current_path_assignment_info and current_path_assignment_info.status == ReassignPathStatus.moving:
                        self.update_path(current_path_assignment_info, ReassignPathStatus.failed)
                        logger.info("Move action,failed ,disk {} path {}.".format(path_assignment_info.disk_name,
                                                                                  path_assignment_info.disk_id,
                                                                                  path_assignment_info.node))

                else:
                    self.update_path(path_assignment_info, ReassignPathStatus.failed)
                    logger.info("Move action ,failed to clean disk {} path {} remotely on node .".format(
                        path_assignment_info.disk_name,
                        path_assignment_info.disk_id,
                        path_assignment_info.node))
        sleep(10)  # wait for display status to user if needed
        logger.info("Process completed.")
        self.remove_assignment()
        ConsulAPI().drop_all_node_sessions(self.__app_conf.get_consul_assignment_path(), config.get_node_name())

    def _clean_iscsi_config(self, disk_id, path_index, iqn):

        logger.debug("Move action ,start clean disk {} path {}.".format(disk_id, path_index))

        lio_api = LioAPI()

        try:

            # Get tpgs for iqn.
            tpgs = lio_api.get_iqns_with_enabled_tpgs().get(iqn, None)
            if not iqn or not tpgs or len(tpgs) == 0:
                logger.info("Move action ,could not find ips for %s " % disk_id)
            # Remove the assigned ips from our interfaces
            elif tpgs and len(tpgs) > 0:
                # Get assigned ips for each path.
                for tpg, ips in tpgs.iteritems():
                    if tpg == str(path_index + 1):
                        lio_api.disable_path(iqn, tpg)
                        logger.info("Move action,cleaned disk {} path {}.".format(disk_id, path_index))
                        break
        except Exception as e:
            logger.error("Move action,could not clean disk path for %s" % disk_id)
            return False
        logger.debug("Move action end clean disk {} path {}.".format(disk_id, path_index))
        return True

    def clean_source_node(self, ip, disk_id):
        if not self.update_path(ip, ReassignPathStatus.moving):
            return False

        # pool = CephAPI().get_pool_bydisk(disk_id)
        pool = self._get_pool_by_disk(disk_id)
        if not pool:
            logger.error('Could not find pool for disk ' + disk_id)
            return False

        disk = CephAPI().get_disk_meta(disk_id,pool)
        paths_list = disk.paths
        disk_path = None
        path_index = -1

        for i in xrange(0, len(paths_list)):
            path_str = paths_list[i]
            path = Path()
            path.load_json(json.dumps(path_str))
            if path.ip == ip:
                disk_path = path
                path_index = i
                break
        if disk_path:
            self._clean_iscsi_config(disk_id, path_index, disk.iqn)
            network = Network()
            NetworkAPI().delete_ip(path.ip, path.eth, path.subnet_mask)
            if network.is_ip_configured(ip):
                logger.error(
                    "Move action,cannot clean newtwork config for disk {} path {}.".format(disk_id, path_index))
                self.update_path(ip, ReassignPathStatus.failed)
                return False
            logger.info("Move action,clean newtwork config for disk {} path {}.".format(disk_id, path_index))
            key = self.__app_conf.get_consul_disks_path() + disk_id + "/" + str(path_index + 1)
            consul_api = ConsulAPI()
            session = self._get_node_session(configuration().get_node_name())
            if ConsulAPI().is_path_locked_by_session(key, session):
                consul_api.release_disk_path(key, session, None)
                logger.info("Move action,release disk {} path {}.".format(disk_id, path_index + 1))
        else:
            self.update_path(ip, ReassignPathStatus.failed)
            return False

        return True

    def update_path(self, ip, status):
        logger.info("Updating path  {} status to {} ".format(ip, status))
        current_reassignments = self.get_current_reassignment()
        if current_reassignments:
            path_assignment_info = current_reassignments.get(ip)
            if path_assignment_info:
                path_assignment_info.status = status
                if ConsulAPI().update_path_assignment(path_assignment_info):
                    logger.info("Path  {} status updated to {} ".format(ip, status))
                    return True
        logger.info("Path  {} status failed to update status to {} ".format(ip, status))
        return False

    def _get_new_plugins_instances(self, modules):

        plugins = []
        for cls in modules:
            try:
                # import plugins module
                mod_obj = __import__(cls)
                for i in str(cls).split(".")[1:]:
                    mod_obj = getattr(mod_obj, i)
                # Find all plugins in module and create instances
                for mod_prop in dir(mod_obj):
                    # Ignore private
                    if not str(mod_prop).startswith("__"):
                        attr = getattr(mod_obj, mod_prop)
                        attr_str = str(attr)
                        attr_type_str = str(type(attr))
                        # Find plugin from type ABCMeta , plugin class name contains 'plugin' and not contains base
                        if attr_type_str.find("ABCMeta") > -1 and attr_str.find("Base") == -1 and attr_str.find(
                                "Plugin"):
                            instance = attr(self.__context)
                plugins.append(instance)
            except Exception as e:
                logger.error("Error load plugin {}.".format(cls))
        return plugins

    def get_forced_paths(self):
        paths = None
        assignments = self._filter_assignments_stats(set_session=True)

        if not assignments.is_reassign_busy:
            return paths

        for path_assignment_info in assignments.paths:
            if path_assignment_info.status == ReassignPathStatus.moving and hasattr(path_assignment_info, "session"):
                if paths is None:
                    paths = dict()
                paths[path_assignment_info.disk_id + "/" + str(path_assignment_info.index)] = path_assignment_info

        return paths

    def _get_node_session(self, node_name):
        logger.info(self.__node_session_dict)
        if self.__session_dict:
            session = self.__node_session_dict.get(node_name)
            if session is not None:
                return session
            else:
                for sess, node in self.__session_dict.iteritems():
                    if node.Node == node_name:
                        self.__node_session_dict[node] = sess
                        return sess


    def _get_pool_by_disk(self,disk_id):
        consul_api = ConsulAPI()
        ceph_api = CephAPI()
        pool = consul_api.get_disk_pool(disk_id)
        if pool:
            logger.info('Found pool:{} for disk:{} via consul'.format(pool,disk_id) )
            return pool
        pool = ceph_api.get_pool_bydisk(disk_id)
        if pool:
            logger.info('Found pool:{} for disk:{} via ceph'.format(pool,disk_id) )
            return pool

        logger.error('Could not find pool for disk ' + disk_id)
        return None