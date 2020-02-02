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
from PetaSAN.core.common.enums import Status
from PetaSAN.core.common.cmd import *
from PetaSAN.core.common.log import logger
from PetaSAN.core.entity.cluster import ClusterInfo, NodeInfo
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.network import Bond


class configuration:
    def __init__(self):
        pass

    def set_password(self, password):
        if call_cmd("echo 'root:" + password + "' | chpasswd"):
            return True
        else:
            return False

    def get_cluster_name(self, custom_name=False):
        if not os.path.exists(ConfigAPI().get_cluster_info_file_path()):
            return ""

        if custom_name:
            return self.get_cluster_info().name

        return "ceph"

    def set_cluster_name(self, cluster_name):
        cluster = ClusterInfo()
        config = ConfigAPI()
        cluster.name = cluster_name

        if not os.path.exists(os.path.dirname(config.get_cluster_info_file_path())):
            os.makedirs(os.path.dirname(config.get_cluster_info_file_path()))

        with open(config.get_cluster_info_file_path(), 'w', ) as f:
            f.write(cluster.write_json())

    def get_cluster_info(self):
        config = ConfigAPI()
        with open(config.get_cluster_info_file_path(), 'r') as f:
            data = json.load(f)
            cluster = ClusterInfo()
            cluster.load_json(json.dumps(data))
            return cluster

    def set_cluster_network_info(self, cluster_info):
        """
        :type cluster_info: ClusterInfo
        """
        cluster_info.name = self.get_cluster_name(True)
        config = ConfigAPI()

        with open(config.get_cluster_info_file_path(), 'w', ) as f:
            f.write(cluster_info.write_json())

    def set_node_info(self, node_info, replace_management=False):
        """
        :type node_info: NodeInfo
        """
        config = ConfigAPI()

        if len(self.get_cluster_info().management_nodes) == 3 and not replace_management:
            node_info.is_management = False

        if not os.path.exists(os.path.dirname(config.get_node_info_file_path())):
            os.makedirs(os.path.dirname(config.get_node_info_file_path()))

        with open(config.get_node_info_file_path(), 'w', ) as f:
            f.write(node_info.write_json())

    def update_node_info(self, node_info, replace_management=False):
        """
        :type node_info: NodeInfo
        """
        config = ConfigAPI()

        with open(config.get_node_info_file_path(), 'w', ) as f:
            f.write(node_info.write_json())

    def get_node_info(self):
        config = ConfigAPI()
        with open(config.get_node_info_file_path(), 'r') as f:
            data = json.load(f)
            node = NodeInfo()
            node.load_json(json.dumps(data))
            return node

    def get_node_name(self):
        import socket
        return socket.gethostname()

    def add_management_node(self):
        """
        :type node_info: NodeInfo
        """
        try:

            ci = self.get_cluster_info()
            ci.management_nodes.append(self.get_node_info())
            self.set_cluster_network_info(ci)

        except Exception as ex:
            logger.error("Cannot add management node")
            return Status().error
        return Status().done

    def get_remote_ips(self, current_node_name):

        current_cluster_info = configuration().get_cluster_info()
        remote_mons_ips = []
        for i in current_cluster_info.management_nodes:
            node_info = NodeInfo()
            node_info.load_json(json.dumps(i))
            if current_node_name != node_info.name:
                remote_mons_ips.append(node_info.management_ip)
        return remote_mons_ips

    def get_remote_nodes_config(self, current_node_name):

        """
        :rtype : [NodeInfo]
        """
        current_cluster_info = configuration().get_cluster_info()
        remote_nodes = []
        for i in current_cluster_info.management_nodes:
            node_info = NodeInfo()
            node_info.load_json(json.dumps(i))
            if current_node_name != node_info.name:
                remote_nodes.append(node_info)
        return remote_nodes

    def is_node_in_cluster_config(self):

        """
        :rtype : [NodeInfo]
        """
        current_cluster_info = configuration().get_cluster_info()
        current_node_name = configuration().get_node_name()
        for i in current_cluster_info.management_nodes:
            node_info = NodeInfo()
            node_info.load_json(json.dumps(i))
            if current_node_name == node_info.name:
                return True
        return False

    def are_all_mgt_nodes_in_cluster_config(self):
        try:
            current_cluster_info = configuration().get_cluster_info()
            if len(current_cluster_info.management_nodes) == 3:
                return True
        except Exception:
            return False
        return False

    def get_management_nodes_config(self):

        """
        :rtype : [NodeInfo]
        """

        nodes = []
        for i in configuration().get_cluster_info().management_nodes:
            node_info = NodeInfo()
            node_info.load_json(json.dumps(i))
            nodes.append(node_info)
        return nodes

    def get_cluster_bonds(self):

        """
        :rtype : [Bond]
        """

        bonds = []
        if not hasattr(configuration().get_cluster_info(), "bonds") or not configuration().get_cluster_info().bonds:
            return bonds
        for i in configuration().get_cluster_info().bonds:
            bond = Bond()
            bond.load_json(json.dumps(i))
            bonds.append(bond)
        return bonds

    def get_template_names(self):
        ls = os.listdir(ConfigAPI().get_tuning_templates_dir_path())
        ls.sort()
        return ls

    def get_template(self, template_name):
        config_api = ConfigAPI()
        template_name = template_name + "/"
        path = config_api.get_tuning_templates_dir_path() + template_name
        tuning_dict = dict()
        ceph_data = "" if not os.path.exists(path + config_api.get_ceph_tunings_file_name()) else \
            open(path + config_api.get_ceph_tunings_file_name(), 'r').read()
        lio_data = "" if not os.path.exists(path + config_api.get_lio_tunings_file_name()) else \
            open(path + config_api.get_lio_tunings_file_name(), 'r').read()
        script_data = "" if not os.path.exists(path + config_api.get_post_deploy_script_file_name()) else \
            open(path + config_api.get_post_deploy_script_file_name(), 'r').read()

        tuning_dict[config_api.get_ceph_tunings_file_name()] = ceph_data
        tuning_dict[config_api.get_lio_tunings_file_name()] = lio_data
        tuning_dict[config_api.get_post_deploy_script_file_name()] = script_data
        return tuning_dict

    def get_ceph_tunings(self):
        config_api = ConfigAPI()
        path = config_api.get_current_tunings_path()
        ceph_data = "" if not os.path.exists(path + config_api.get_ceph_tunings_file_name()) else \
            open(path + config_api.get_ceph_tunings_file_name(), 'r').read()
        ceph_data = ceph_data.replace("[global]", "")
        return ceph_data

    def get_lio_backstore_tunings(self):
        config_api = ConfigAPI()
        path = config_api.get_current_tunings_path()
        data = None if not os.path.exists(path + config_api.get_lio_tunings_file_name()) else \
            open(path + config_api.get_lio_tunings_file_name(), 'r').read()

        if data:
            data = json.loads(str(data))
            if data.get("storage_objects", None) and len(data["storage_objects"]) > 0 \
                    and data["storage_objects"][0].get("attributes", None):
                return data["storage_objects"][0]["attributes"]

        return None

    def get_lio_tpg_tuning_attributes(self):
        config_api = ConfigAPI()
        path = config_api.get_current_tunings_path()
        data = None if not os.path.exists(path + config_api.get_lio_tunings_file_name()) else \
            open(path + config_api.get_lio_tunings_file_name(), 'r').read()

        if data:
            data = json.loads(str(data))
            if data.get("targets", None) and len(data["targets"]) > 0 and data["targets"][0].get("tpgs", None):
                tpgs = data["targets"][0].get("tpgs", None)
                if len(tpgs) > 0 and tpgs[0].get("attributes", None):
                    return tpgs[0]["attributes"]

        return None

    def get_lio_tpg_tuning_parameters(self):
        config_api = ConfigAPI()
        path = config_api.get_current_tunings_path()
        data = None if not os.path.exists(path + config_api.get_lio_tunings_file_name()) else \
            open(path + config_api.get_lio_tunings_file_name(), 'r').read()

        if data:
            data = json.loads(str(data))
            if data.get("targets", None) and len(data["targets"]) > 0 and data["targets"][0].get("tpgs", None):
                tpgs = data["targets"][0].get("tpgs", None)
                if len(tpgs) > 0 and tpgs[0].get("parameters", None):
                    return tpgs[0]["parameters"]

        return None

    def save_current_tunings(self, ceph, lio, post_script, storage_engine):
        config_api = ConfigAPI()
        path = config_api.get_current_tunings_path()

        if not os.path.exists(path):
            os.makedirs(path)
        with open(path + config_api.get_ceph_tunings_file_name(), 'w', ) as f:
            f.write(ceph)

        with open(path + config_api.get_lio_tunings_file_name(), 'w', ) as f:
            f.write(lio)

        with open(path + config_api.get_post_deploy_script_file_name(), 'w', ) as f:
            f.write(post_script)
        logger.info("Current tuning configurations saved.")

        # Save "storage_engine" in Cluster info #
        # ------------------------------------- #
        try:
            ci = self.get_cluster_info()
            ci.storage_engine = storage_engine
            self.set_cluster_network_info(ci)

        except Exception as ex:
            logger.error("Cannot add storage engine to cluster info , {}".format(ex.message))
