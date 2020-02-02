#!/usr/bin/env python
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

from PetaSAN.core.cluster.configuration import configuration
import os
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI



cluster_name = configuration().get_cluster_name()
node_info = configuration().get_node_info()
node_name = node_info.name
nodes = configuration().get_management_nodes_config()
collected_path = ConfigAPI().get_collect_state_dir()+node_name


if not os.path.exists("{}".format(ConfigAPI().get_collect_state_dir())):
    os.system("mkdir {}".format(ConfigAPI().get_collect_state_dir()))
if os.path.exists(collected_path):
    os.system("rm -rf {}".format(collected_path))
if os.path.exists("{}.tar".format(collected_path)):
    os.system("rm -rf {}.tar".format(collected_path))
os.mkdir("{}".format(collected_path))


try:
    for node in nodes:
        if node.name == node_info.name:
            continue
        else:
            os.system("echo '                                  ' >> {}/pinging".format(collected_path))
            os.system("ping -c 4 {} >> {}/pinging ".format(node.management_ip,collected_path))
            os.system("ping -c 4 {} >> {}/pinging ".format(node.backend_1_ip,collected_path))
            os.system("ping -c 4 {} >> {}/pinging ".format(node.backend_2_ip,collected_path))
            os.system("echo '------------------------------------------' >> {}/pinging".format(collected_path))

except Exception as e:
    logger.exception("error in pinging subnets ips")

os.system("ip address > {}/ip_address".format(collected_path))
os.system("consul members > {}/consul_members".format(collected_path))
os.system("ceph-volume lvm list > {}/ceph_volume_list".format(collected_path))
os.system("ceph status --cluster {} > {}/cluster_status".format(cluster_name,collected_path))
os.system("ceph osd tree --cluster {} > {}/ceph_osd_tree".format(cluster_name,collected_path))
os.system("ceph osd dump --cluster {} > {}/ceph_osd_dump".format(cluster_name,collected_path))
os.system("ls /sys/class/net > {}/eth_list".format(collected_path))
os.system("lspci -v > {}/pci_list".format(collected_path))
os.system("dmesg > {}/dmesg ".format(collected_path))
os.system("cp {} {}".format(ConfigAPI().get_cluster_info_file_path(),collected_path))
os.system("cp /etc/hosts {}".format(collected_path))
os.system("cp {} {}".format(ConfigAPI().get_log_file_path(),collected_path))
os.system("cp {} {}".format(ConfigAPI().get_node_info_file_path(),collected_path))
os.system("cp -r /opt/petasan/scripts/jobs {}".format(collected_path))
try:
    os.system("tar -cPvf {}.tar {}".format(collected_path,collected_path))
except:
    logger.exception("error compress state files")

os.system("rm -rf {}".format(collected_path))



