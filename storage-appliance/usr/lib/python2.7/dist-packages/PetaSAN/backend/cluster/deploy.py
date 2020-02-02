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

# from flask import json
# import os
from PetaSAN.backend.file_sync_manager import FileSyncManager
from PetaSAN.core.ceph.deploy.build import *
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.cluster.ntp import NTPConf
from PetaSAN.core.cluster.sharedfs import SharedFS

from PetaSAN.core.common.CustomException import SSHKeyException, JoinException, ReplaceException
from PetaSAN.core.common.enums import Status, BuildStatus
from PetaSAN.core.common.log import logger
from PetaSAN.core.consul.deploy.build import build_consul, clean_consul_local, build_consul_client, \
    replace_consul_leader
from PetaSAN.core.consul.deploy.build import clean_consul
from PetaSAN.core.ssh.ssh import ssh
from PetaSAN.core.cluster.network import Network
from PetaSAN.core.entity.cluster import ClusterInfo, NodeInfo, PreConfigStorageDisks
from PetaSAN.core.config.api import ConfigAPI
# PetaSAN.core.consul.deploy.build.ConsulLeaderStarter
from PetaSAN.core.common.enums import JoiningStatus
from PetaSAN.core.consul.base import BaseAPI


class Wizard:
    def __init__(self):
        pass

    def get_node_status(self):
        config_api = ConfigAPI()
        root_path = config_api.get_consul_nodes_path()
        node_status = JoiningStatus.not_joined
        if os.path.exists(config_api.get_replace_file_path()):
            return node_status
        try:
            # Config
            try:
                config = configuration()
                node_name = config.get_node_info().name
            except Exception as config_exc:
                logger.exception("Config file error. The PetaSAN os maybe just installed.")
                return node_status
            try:
                cluster_info = config.get_cluster_info().management_nodes
                mgmt_nodes_count = cluster_info.__len__()

                if mgmt_nodes_count < 3:
                    raise Exception("Cluster is not completed, PetaSAN will check node join status.")

                consul_base = BaseAPI()
                data = consul_base.read_value(root_path + node_name)

                if data is not None and configuration().are_all_mgt_nodes_in_cluster_config():
                    return JoiningStatus.node_joined
                else:
                    return JoiningStatus.not_joined

            except Exception as exc:
                cluster_info = config.get_cluster_info().management_nodes
                mgmt_nodes_count = cluster_info.__len__()
                logger.exception(exc.message)

                if mgmt_nodes_count < 3 and not config.is_node_in_cluster_config():
                    return JoiningStatus.not_joined
                elif mgmt_nodes_count is 3 and config.is_node_in_cluster_config():
                    return JoiningStatus.node_joined

                if mgmt_nodes_count is 1:
                    return JoiningStatus.one_node_exists
                elif mgmt_nodes_count is 2:
                    return JoiningStatus.two_node_exist

        except Exception as e:
            return JoiningStatus.not_joined
        return node_status

    def create_cluster_info(self, password, cluster_name):
        config = configuration()
        ssh_obj = ssh()
        try:
            ssh_obj.create_id(True)
            ssh_obj.create_authorized_key_file()
            logger.info("Created keys for cluster {}".format(cluster_name))
            config.set_cluster_name(cluster_name)
            logger.info("Created cluster file and set cluster name to {}".format(cluster_name))

            Network().clean_bonding()
            if not config.set_password(password):
                logger.error("Could not set root password.")
                return Status().error
            logger.info("password set successfully.")

        except Exception as ex:
            logger.exception(ex.message)
            return Status().error
        return Status().done

    def get_node_eths(self):
        net = Network()
        management = net.get_node_management_interface()
        eths = net.get_node_interfaces()

        for i in eths:
            if i.name == management:
                i.is_management = True
                break
        return eths

    def set_cluster_interface(self, bonds=[], jumbo_frames_eths=[]):
        try:
            if (not bonds or len(bonds) == 0) and (not jumbo_frames_eths or len(jumbo_frames_eths) == 0):
                return Status().done
            config = configuration()
            cluster_info = config.get_cluster_info()

            cluster_info.bonds = bonds
            cluster_info.jumbo_frames = jumbo_frames_eths
            config.set_cluster_network_info(cluster_info)
            logger.info("Updated cluster interface successfully.")

        except Exception as ex:
            logger.exception(ex.message)
            return Status().error

        return Status().done

    def reset_cluster_interface(self):
        try:
            config = configuration()
            cluster_info = config.get_cluster_info()

            cluster_info.bonds = []
            cluster_info.jumbo_frames = []
            config.set_cluster_network_info(cluster_info)
            logger.info("Updated cluster interface successfully.")

        except Exception as ex:
            logger.exception(ex.message)
            return Status().error
        return Status().done

    def set_cluster_network_info(self, cluster_info):
        """
        :type cluster_info: ClusterInfo
        """
        try:
            config = configuration()
            net = Network()
            current_cluster_info = config.get_cluster_info()
            cluster_info.name = current_cluster_info.name
            cluster_info.bonds = current_cluster_info.bonds
            cluster_info.jumbo_frames = current_cluster_info.jumbo_frames
            cluster_info.eth_count = len(net.get_node_interfaces())
            cluster_info.management_eth_name = net.get_node_management_interface()
            config.set_cluster_network_info(cluster_info)
            logger.info("Updated cluster network successfully.")

        except Exception as ex:
            logger.exception(ex.message)
            return Status().error
        return Status().done

    def is_valid_network_setting(self):
        config = configuration().get_cluster_info()
        net = Network()
        eths = net.get_node_interfaces()
        try:
            if config.eth_count != len(eths):
                return False
            elif config.management_eth_name != net.get_node_management_interface():
                return False
            else:
                return True
        except Exception as ex:
            logger.exception(ex.message)
            return False

    def set_node_info(self, node_info):
        """
        :type node_info: NodeInfo
        """
        try:
            config = configuration()
            net = Network()
            node_info.name = config.get_node_name()
            node_info.management_ip = net.get_node_management_ip()
            config.set_node_info(node_info)
            config_api = ConfigAPI()

            if call_script(config_api.get_node_start_ips_script_path()) != 0:
                raise Exception("Error could not start backend network.")
            logger.info("Set node info completed successfully.")

        except Exception as ex:
            logger.exception(ex.message)
            return Status().error

        return Status().done

    def set_node_info_role(self, is_storage, is_iscsi, is_backup):
        """
        :param is_storage: bool
        :param is_iscsi: bool
        :param is_backup: bool
        """
        try:
            config = configuration()
            current_node_info = config.get_node_info()
            current_node_info.is_storage = is_storage
            current_node_info.is_iscsi = is_iscsi
            current_node_info.is_backup = is_backup
            config.set_node_info(current_node_info)
            logger.info("Set node role completed successfully.")

        except Exception as ex:
            logger.exception(ex.message)
            return Status().error
        return Status().done

    def join(self, ip, password):
        config = configuration()
        ssh_obj = ssh()
        config_api = ConfigAPI()

        if os.path.exists(config_api.get_cluster_info_file_path()):
            os.remove(config_api.get_cluster_info_file_path())
        Network().clean_bonding()
        logger.info("Starting node join")

        if ssh_obj.copy_public_key_from_host(ip, password):
            logger.info("Successfully copied public keys.")
            if ssh_obj.copy_private_key_from_host(ip, password):
                ssh_obj.create_authorized_key_file()
                logger.info("Successfully copied private keys.")
                config.set_password(password)
                logger.info("password set successfully.")

        else:
            raise SSHKeyException("Error while copying keys or setting password.")

        if not ssh_obj.call_command(ip, "python {}".format(config_api.get_cluster_status_for_join_path())):
            raise JoinException("ceph monitor status not healthy.")

        if not os.listdir(os.path.dirname(config_api.get_cluster_info_file_path())):
            os.makedirs(os.path.dirname(config_api.get_cluster_info_file_path()))
        logger.info("Start copying  cluster info file.")

        if not ssh_obj.copy_file_from_host(ip, config_api.get_cluster_info_file_path()):
            raise Exception("Error while copy cluster info file.")
        logger.info("Successfully copied cluster info file.")

        cluster_name = config.get_cluster_name(True)
        logger.info("Joined cluster {}".format(cluster_name))
        self.__copy_current_tunings(ip)
        return cluster_name

    def get_cluster_name(self):
        cluster_config = configuration()
        return cluster_config.get_cluster_info().name

    def build(self):
        try:
            self.__status_report = StatusReport()
            conf = configuration()

            if len(conf.get_cluster_info().management_nodes) == 0:
                node_num = len(conf.get_cluster_info().management_nodes) + 1
                self.__status_report.nod_num = node_num
                NTPConf().setup_ntp_local()
                if conf.add_management_node() != Status().done:
                    self.__status_report.success = False
                    self.__status_report.failed_tasks.append("core_cluster_deploy_cant_add_node")

                logger.info("Node 1 added, cluster requires 2 other nodes to build.")
                self.run_post_deploy_script()
                return BuildStatus().OneManagementNode

            elif len(conf.get_cluster_info().management_nodes) == 1:
                node_num = len(conf.get_cluster_info().management_nodes) + 1
                self.__status_report.nod_num = node_num

                connection_status = self.check_connections()
                if not connection_status.success:
                    self.__status_report.failed_tasks.extend(connection_status.failed_tasks)
                    logger.error("Connection ping error.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().connection_error

                NTPConf().setup_ntp_local()

                if conf.add_management_node() != Status().done:
                    self.__status_report.success = False
                    self.__status_report.failed_tasks.append("core_cluster_deploy_cant_add_node")
                    return BuildStatus().error
                if not self.__sync_cluster_config_file():
                    return BuildStatus().error

                logger.info("Node 2 is added, cluster requires 1 other node to build.")
                self.run_post_deploy_script()
                return BuildStatus().TwoManagementNodes

            elif len(conf.get_cluster_info().management_nodes) == 2:
                node_num = len(conf.get_cluster_info().management_nodes) + 1
                self.__status_report.nod_num = node_num

                connection_status = self.check_connections()
                if not connection_status.success:
                    self.__status_report.failed_tasks.extend(connection_status.failed_tasks)
                    logger.error("Connection ping error.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().connection_error

                status = self.check_remote_connection()
                if not status.success:
                    self.__status_report = status
                    return BuildStatus().error

                NTPConf().setup_ntp_local()

                logger.info("Stopping petasan services on all nodes.")
                self.stop_petasan_services()
                logger.info("Starting local clean_ceph.")
                clean_ceph()
                logger.info("Starting local clean_consul.")
                clean_consul()

                status = build_consul()
                if not status.success:
                    self.__status_report.failed_tasks.extend(status.failed_tasks)
                    logger.error("Could not build consul.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().build_consul_error

                status = build_monitors()
                if not status.success:
                    self.__status_report = status
                    logger.error("Could not build ceph monitors.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().build_monitors_error

                status = build_osds()
                if not status.success:
                    self.__status_report = status
                    logger.error("Could not build ceph OSDs.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().build_osd_error
                else:
                    self.__status_report.failed_tasks.extend(status.failed_tasks)

                logger.info("Main core components deployed.")

                if not self.__commit_management_nodes():
                    self.__status_report.success = False
                    logger.error("Could not commit node.")
                    self.__status_report.failed_tasks.append("core_cluster_deploy_couldnt_commit_node")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().error

                logger.info("Starting all services.")
                self.start_petasan_services()

                if not self.add__node_to_hosts_file():
                    self.__status_report.success = False
                    logger.error("Could not add node to hosts file.")
                    self.__status_report.failed_tasks.append("core_cluster_deploy_couldnt_add_node_hosts")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().error

                SharedFS().setup_management_nodes()

                if conf.add_management_node() != Status().done:
                    self.__status_report.success = False
                    self.__status_report.failed_tasks.append("core_cluster_deploy_couldnt_add_node_config")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().error

                logger.info("Updating rbd pool.")
                if not create_rbd_pool():
                    self.__status_report.success = False
                    self.__status_report.failed_tasks.append("core_cluster_deploy_couldnt_update_rbd")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().error

                logger.info("Creating EC Profiles.")
                if not create_ec_profiles():
                    self.__status_report.success = False
                    self.__status_report.failed_tasks.append("core_cluster_deploy_couldnt_create_ec_profiles")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().error

                logger.info("Waiting for ceph to reach active and clean status.")
                test_active_clean()
                if not self.__sync_cluster_config_file():
                    return BuildStatus().error

                self.run_post_deploy_script()
                self.kill_petasan_console(True)
                logger.info("Node 3 added and cluster is now ready.")

            elif len(conf.get_cluster_info().management_nodes) == 3 and not os.path.exists(
                    ConfigAPI().get_replace_file_path()):
                # ------------------------------ Join ------------------------------ #
                # ------------------------------------------------------------------ #
                node_num = len(conf.get_cluster_info().management_nodes) + 1
                self.__status_report.nod_num = node_num
                logger.info("Joining node to running cluster.")

                connection_status = self.check_connections()
                if not connection_status.success:
                    self.__status_report.failed_tasks.extend(connection_status.failed_tasks)
                    logger.error("Connection ping error.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().connection_error

                status = self.check_remote_connection()
                NTPConf().setup_ntp_local()

                if not status.success:
                    self.__status_report = status
                    return BuildStatus().error

                logger.info("Stopping petasan services on local node.")
                self.stop_petasan_services(remote=False)
                logger.info("Starting local clean_ceph.")
                clean_ceph_local()
                logger.info("Starting local clean_consul.")
                clean_consul_local()

                status = build_consul_client()
                if not status.success:
                    self.__status_report.failed_tasks.extend(status.failed_tasks)
                    logger.error("Could not build consul client.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().build_consul_error

                status = copy_ceph_config_from_mon()
                if not status.success:
                    self.__status_report.failed_tasks.extend(status.failed_tasks)
                    logger.error("Could not copy ceph config.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().build_consul_error

                status = create_osds_local()
                if not status.success:
                    self.__status_report = status
                    logger.error("Could not build ceph OSDs.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().build_osd_error
                else:
                    self.__status_report.failed_tasks.extend(status.failed_tasks)

                logger.info("Main core components deployed.")
                logger.info("Staring all services")
                self.start_petasan_services(remote=False)
                test_active_clean()
                if not self.__commit_local_node():
                    test_active_clean()
                    if not self.__commit_local_node():
                        self.__status_report.success = False
                        logger.error("Could not commit node.")
                        self.__status_report.failed_tasks.append("core_cluster_deploy_couldnt_commit_node_join")
                        logger.error(self.__status_report.failed_tasks)
                        os.remove(ConfigAPI().get_cluster_info_file_path())
                        return BuildStatus().error

                if not self.add__node_to_hosts_file(remote=False):
                    test_active_clean()
                    if not self.add__node_to_hosts_file(remote=False):
                        self.__status_report.success = False
                        logger.error("Could not add node to hosts file.")
                        self.__status_report.failed_tasks.append("core_cluster_deploy_couldnt_add_node_hosts")
                        logger.error(self.__status_report.failed_tasks)
                        os.remove(ConfigAPI().get_cluster_info_file_path())
                        return BuildStatus().error

                logger.info("Node successfully joined to cluster.")
                self.kill_petasan_console(False)
                if os.path.exists(ConfigAPI().get_replace_file_path()):
                    os.remove(ConfigAPI().get_replace_file_path())

                self.run_post_deploy_script()
                return BuildStatus().done_joined

            elif len(conf.get_cluster_info().management_nodes) == 3 and os.path.exists(
                    ConfigAPI().get_replace_file_path()):
                # ----------------------------- Replace ---------------------------- #
                # ------------------------------------------------------------------ #
                node_num = len(conf.get_cluster_info().management_nodes) + 1
                self.__status_report.nod_num = node_num
                logger.info("Replace node is starting.")

                connection_status = self.check_connections()
                if not connection_status.success:
                    self.__status_report.failed_tasks.extend(connection_status.failed_tasks)
                    logger.error("Connection ping error.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().connection_error

                status = self.check_remote_connection()
                NTPConf().setup_ntp_local()

                if not status.success:
                    self.__status_report = status
                    return BuildStatus().error

                logger.info("Stopping petasan services on local node.")
                self.stop_petasan_services(remote=False)
                logger.info("Starting clean_ceph.")
                clean_ceph_local()
                logger.info("Starting local clean_consul.")
                clean_consul_local()

                status = replace_consul_leader()
                if not status.success:
                    self.__status_report.failed_tasks.extend(status.failed_tasks)
                    logger.error("Could not replace consul leader.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().build_consul_error

                status = replace_local_monitor()
                if not status.success:
                    self.__status_report.failed_tasks.extend(status.failed_tasks)
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().build_monitors_error

                status = create_osds_local()
                if not status.success:
                    self.__status_report = status
                    logger.error("Could not build ceph OSDs.")
                    logger.error(self.__status_report.failed_tasks)
                    return BuildStatus().build_osd_error
                else:
                    self.__status_report.failed_tasks.extend(status.failed_tasks)

                logger.info("Main core components deployed.")
                logger.info("Starting all services.")
                self.start_petasan_services(remote=False)
                test_active_clean()

                SharedFS().rebuild_management_node()

                logger.info("Node successfully added to cluster.")
                self.run_post_deploy_script()
                self.kill_petasan_console(False)
                os.remove(ConfigAPI().get_replace_file_path())
                return BuildStatus().done_replace

        except Exception as ex:
            config_api = ConfigAPI()
            if os.path.exists(config_api.get_cluster_info_file_path()):
                os.remove(config_api.get_cluster_info_file_path())
            logger.exception(ex.message)
            return BuildStatus().error

        return BuildStatus().done

    def __sync_cluster_config_file(self):
        try:
            manage_conf = configuration()
            current_node_name = manage_conf.get_node_info().name
            cluster_info = manage_conf.get_cluster_info()
            config_api = ConfigAPI()

            for i in cluster_info.management_nodes:
                node_info = NodeInfo()
                node_info.load_json(json.dumps(i))

                if node_info.name != current_node_name:
                    ssh_obj = ssh()
                    if not ssh_obj.copy_file_to_host(node_info.management_ip, config_api.get_cluster_info_file_path()):
                        logger.error("Could not copy configuration file to {} server.".format(node_info.name))
                        self.__status_report.success = False
                        self.__status_report.failed_tasks.append("core_cluster_deploy_couldnt_sync_config_file")
                        return False

        except Exception as ex:
            logger.exception(ex.message)
            self.__status_report.success = False
            self.__status_report.failed_tasks.append("core_cluster_deploy_couldnt_sync_config_file")
            return False

        # copy_file_to_host
        return True

    consul_server_conf = '/etc/consul.d/server'
    data_dir = '/var/consul'
    consul_server_conf_file = '/etc/consul.d/server/config.json'
    __status_report = StatusReport()

    def get_status_reports(self):
        return self.__status_report

    def check_remote_connection(self):
        cluster_conf = configuration()
        ips = cluster_conf.get_remote_ips(cluster_conf.get_node_name())
        ssh_obj = ssh()
        status = StatusReport()
        for i in ips:
            if not ssh_obj.check_ssh_connection(str(i)):
                status.success = False
                status.failed_tasks.append("core_cluster_deploy_ip_couldnt_connect" + "%" + i)
                return status

        return status

    def get_node_name(self):
        return configuration().get_node_name()

    def __commit_management_nodes(self):
        if self.__commit_local_node():
            if self.__commit_remote_nodes():
                return self.__commit_cluster_info()
        return False

    def __commit_local_node(self):
        confi_api = ConfigAPI()
        consul_base_api = BaseAPI()
        cluster_conf = configuration()
        try:
            consul_base_api.write_value(confi_api.get_consul_nodes_path() + cluster_conf.get_node_name(),
                                        cluster_conf.get_node_info().write_json())
        except Exception as ex:
            logger.exception(ex.message)
            return False
        return True

    def __commit_cluster_info(self):
        confi_api = ConfigAPI()
        consul_base_api = BaseAPI()
        cluster_conf = configuration()
        try:
            consul_base_api.write_value(confi_api.get_consul_cluster_info_path(),
                                        cluster_conf.get_cluster_info().write_json())
        except Exception as ex:
            logger.exception(ex.message)
            return False
        return True

    def __commit_remote_nodes(self):
        confi_api = ConfigAPI()
        consul_base_api = BaseAPI()
        cluster_conf = configuration()
        try:
            for node in cluster_conf.get_remote_nodes_config(cluster_conf.get_node_name()):
                consul_base_api.write_value(confi_api.get_consul_nodes_path() + node.name,
                                            node.write_json())
        except Exception as ex:
            logger.exception(ex.message)
            return False
        return True

    def start_petasan_services(self, remote=True):
        cluster_conf = configuration()
        ssh_obj = ssh()
        exec_command("python {} build ".format(ConfigAPI().get_startup_petasan_services_path()))
        sleep(5)
        if not remote:
            return
        try:
            for ip in cluster_conf.get_remote_ips(cluster_conf.get_node_name()):
                ssh_obj.exec_command(ip, "python {} build ".format(ConfigAPI().get_startup_petasan_services_path()))
                sleep(5)
        except Exception as ex:
            logger.exception(ex.message)
            raise ex

    def stop_petasan_services(self, remote=True):
        logger.info("Stopping all petasan services.")
        cluster_conf = configuration()
        ssh_obj = ssh()
        exec_command("python {} ".format(ConfigAPI().get_stop_petasan_services_path()))
        if not remote:
            return
        try:
            for ip in cluster_conf.get_remote_ips(cluster_conf.get_node_name()):
                ssh_obj.exec_command(ip, "python {}".format(ConfigAPI().get_stop_petasan_services_path()))
        except Exception as ex:
            logger.exception(ex.message)
            raise ex

    def add__node_to_hosts_file(self, remote=True):
        path = "/etc/hosts"

        cluster_conf = configuration()
        current_node = cluster_conf.get_node_info()

        try:
            with open(path, mode='a') as f:
                f.write("{ip}   {host}\n".format(ip=current_node.management_ip, host=current_node.name))
                if remote:
                    f.write("127.0.0.1   localhost\n")
                    for node in cluster_conf.get_remote_nodes_config(current_node.name):
                        f.write("{ip}   {host}\n".format(ip=node.management_ip, host=node.name))

            if FileSyncManager().commit_file(path):
                return True

        except Exception as e:
            logger.error("Could not write hosts file.")

        return False

    def get_management_urls(self):
        url = []
        for i in configuration().get_management_nodes_config():
            url.append("http://{}:5000/".format(i.management_ip))
        return url

    def is_cluster_config_complated(self):
        return configuration().are_all_mgt_nodes_in_cluster_config()

    def get_node_deploy_url(self):
        try:
            ip = configuration().get_node_info().management_ip
        except Exception as e:
            ip = Network().get_node_management_ip()
        return "http://{}:5001/".format(ip)

    def kill_petasan_console(self, remote=True):
        cluster_conf = configuration()
        ssh_obj = ssh()
        exec_command("python {} ".format(ConfigAPI().get_kill_console_script_path()))
        if not remote:
            return
        try:
            for ip in cluster_conf.get_remote_ips(cluster_conf.get_node_name()):
                ssh_obj.exec_command(ip, "python {} ".format(ConfigAPI().get_kill_console_script_path()))
        except Exception as ex:
            logger.exception(ex.message)
            raise ex

    def replace(self, ip, password):
        config = configuration()
        ssh_obj = ssh()
        config_api = ConfigAPI()
        logger.info("Starting replace.")
        if os.path.exists(config_api.get_cluster_info_file_path()):
            os.remove(config_api.get_cluster_info_file_path())

        if ssh_obj.copy_public_key_from_host(ip, password):
            logger.info("Successfully copied public keys.")
            if ssh_obj.copy_private_key_from_host(ip, password):
                ssh_obj.create_authorized_key_file()
                logger.info("Successfully copied private keys.")

        else:
            raise SSHKeyException("Error copying keys")

        out, err = ssh_obj.exec_command(ip, "python {}".format(config_api.get_cluster_status_for_join_path()))
        out = int(out)
        if out == -1:
            raise ReplaceException("core_deploy_replace_mon_not_healthy_err")
        elif out == 0:
            raise ReplaceException("core_deploy_replace_cluster_in_progress_err")
        elif out == 1:
            raise ReplaceException("core_deploy_replace_two_management_node_down_err")
        elif out == 3:
            raise ReplaceException("core_deploy_replace_cluster_running_err")

        if not os.listdir(os.path.dirname(config_api.get_cluster_info_file_path())):
            os.makedirs(os.path.dirname(config_api.get_cluster_info_file_path()))

        logger.info("Starting to copy config file")
        if not ssh_obj.copy_file_from_host(ip, config_api.get_cluster_info_file_path()):
            raise Exception("Error copying  config file")

        logger.info("Successfully copied config file.")
        cluster_name = config.get_cluster_name(True)
        logger.info("Successfully joined to cluster {}".format(cluster_name))

        wrong_name = True
        wrong_ip = True
        for node_info in config.get_management_nodes_config():
            if node_info.name == config.get_node_name() or node_info.management_ip == Network().get_node_management_ip():
                if node_info.name == config.get_node_name():
                    wrong_name = False

                if node_info.management_ip == Network().get_node_management_ip():
                    wrong_ip = False

                if not wrong_name and not wrong_ip:
                    config.set_node_info(node_info, True)
                    open(config_api.get_replace_file_path(), 'w+').close()
                break

        if wrong_name and wrong_ip:
            os.remove(config_api.get_cluster_info_file_path())
            raise ReplaceException("core_deploy_replace_node_do_not_match_err")
        elif wrong_name:
            os.remove(config_api.get_cluster_info_file_path())
            raise ReplaceException("core_deploy_replace_node_do_not_match_name_err")
        elif wrong_ip:
            os.remove(config_api.get_cluster_info_file_path())
            raise ReplaceException("core_deploy_replace_node_do_not_match_ip_err")

        config.set_password(password)
        logger.info("password set successfully.")
        self.__copy_current_tunings(ip)
        return cluster_name

    def start_node_backend_networks(self):
        config_api = ConfigAPI()
        try:
            if call_script(config_api.get_node_start_ips_script_path()) != 0:
                raise Exception("Error starting backend networks")

        except Exception as ex:
            return Status().error

    def get_template_names(self):
        return configuration().get_template_names()

    def get_template(self, template_name):
        return configuration().get_template(template_name)

    def save_current_tuning(self, ceph, lio, post_script):
        configuration().save_current_tunings(ceph, lio, post_script)

    def run_post_deploy_script(self):
        config_api = ConfigAPI()
        path = config_api.get_current_tunings_path() + config_api.get_post_deploy_script_file_name()
        if os.path.exists(path):
            call_cmd("chmod +x {}".format(path))
            logger.info("Run post deploy script.")
            call_cmd(path)

    def __copy_current_tunings(self, ip):
        config_api = ConfigAPI()
        ssh_obj = ssh()
        path = config_api.get_current_tunings_path()
        post_deploy_script_path = path + config_api.get_post_deploy_script_file_name()
        ceph_path = path + config_api.get_ceph_tunings_file_name()
        lio_path = path + config_api.get_lio_tunings_file_name()
        ssh_obj.copy_file_from_host(ip, post_deploy_script_path)
        ssh_obj.copy_file_from_host(ip, ceph_path)
        ssh_obj.copy_file_from_host(ip, lio_path)

    def set_node_storage_disks(self, osds, journals, caches):
        config_api = ConfigAPI()
        if os.path.exists(config_api.get_node_pre_config_disks()):
            os.remove(config_api.get_node_pre_config_disks())
        disks = PreConfigStorageDisks()
        disks.osds = osds
        disks.journals = journals
        disks.caches = caches
        with open(ConfigAPI().get_node_pre_config_disks(), 'w', ) as f:
            f.write(disks.write_json())

    def check_connections(self):
        '''
        to get all ips of management, backend1 and backend2 and ping them
        :param:
        :return:list of all possible ping errors
        '''

        current_cluster_info = configuration().get_cluster_info()
        management_nodes = current_cluster_info.management_nodes
        status_report = StatusReport()
        status_report.success = True

        for node in management_nodes:
            node_info = NodeInfo()
            node_info.load_json(json.dumps(node))
            management_host = node_info.management_ip
            backend1_host = node_info.backend_1_ip
            backend2_host = node_info.backend_2_ip

            if not Network().ping(management_host):
                status_report.failed_tasks.append(
                    'core_deploy_ping_error_node_{}_management'.format(management_nodes.index(node) + 1))
            if not Network().ping(backend1_host):
                status_report.failed_tasks.append(
                    'core_deploy_ping_error_node_{}_backend1'.format(management_nodes.index(node) + 1))
            if not Network().ping(backend2_host):
                status_report.failed_tasks.append(
                    'core_deploy_ping_error_node_{}_backend2'.format(management_nodes.index(node) + 1))
            if len(status_report.failed_tasks) > 0:
                status_report.success = False

        return status_report

    def get_interfaces_info(self):
        '''
        to get all network interfaces info
        :param:
        :return: dictionary of all interfaces with their info
        '''

        # Define "interfaces_info" dictionary which will contain interfaces names as Keys , and the value of each key
        # will be dictionary of interface info :
        # { 'eth0': {'device': '...', 'mac': '...', 'pci': '...', 'model': '...'} ,
        #   'eth1': {'device': '...', 'mac': '...', 'pci': '...', 'model': '...'} ,
        #   'eth2': {'device': '...', 'mac': '...', 'pci': '...', 'model': '...'}   }

        interfaces_info = {}

        config_api = ConfigAPI()
        script_path = config_api.get_detect_interfaces_script_path()
        ret1, stdout1, stderr1 = exec_command_ex(script_path)

        if ret1 != 0:
            if stderr1:
                logger.error("Cannot detect network interfaces info , {}".format(str(stderr1)))
                raise Exception("Cannot detect network interfaces info")

        stdout1 = stdout1.rstrip()
        devices_ls = stdout1.splitlines()

        for device_info in devices_ls:
            # Define "interface_info" dictionary which will contain interface's info :
            interface_info = {}
            device_name = ""

            device_info_ls = device_info.split(",")

            for info_item in device_info_ls:
                info_item_ls = info_item.split("=")

                # get device name :
                if 'device' in info_item_ls:
                    device_name = info_item_ls[1]

                interface_info[info_item_ls[0]] = info_item_ls[1]

            interfaces_info[device_name] = interface_info

        return interfaces_info

