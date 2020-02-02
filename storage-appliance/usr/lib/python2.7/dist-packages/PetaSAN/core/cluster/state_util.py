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
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.ssh.ssh import ssh
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.cmd import call_cmd
from PetaSAN.core.common.log import logger


class StateUtil():

    def collect_local_node_state(self):
        script_path = ConfigAPI().get_collect_state_script()
        node_name=configuration().get_node_name()
        command = "python {}".format(script_path)
        if call_cmd(command):
            logger.info("execute collect script on {}".format(node_name))
            return True
        return False


    def collect_remote_nodes_state(self):
        script_path = ConfigAPI().get_collect_state_script()
        if not os.path.exists("{}".format(ConfigAPI().get_collect_state_dir())):
            os.system("mkdir {}".format(ConfigAPI().get_collect_state_dir()))
        cmd = "python {}".format(script_path)
        ssh_obj= ssh()
        remote_nodes = configuration().get_remote_nodes_config(configuration().get_node_name())
        for node in remote_nodes:
           if ssh_obj.call_command(node.management_ip,cmd):
                logger.info("execute collect script on {}".format(node.name))
                compress_file=ConfigAPI().get_collect_state_dir()+node.name+".tar"
                if not ssh_obj.copy_file_from_host(node.management_ip,compress_file):
                    logger.error("error copy files from remote nodes")
                    return False
        return True



    def collect_all(self):
            self.collect_local_node_state()
            self.collect_remote_nodes_state()
            cluster_name = configuration().get_cluster_name()
            cluster_file = '/opt/petasan/log/{}'.format(cluster_name)
            try:
                    os.system("tar -cPvf {}.tar {}".format(cluster_file,ConfigAPI().get_collect_state_dir()))
                    logger.info("collect management nodes state successfully")
                    os.system("rm -rf {}".format(ConfigAPI().get_collect_state_dir()))
                    return True
            except:
                logger.exception("error compress state files")
                return False