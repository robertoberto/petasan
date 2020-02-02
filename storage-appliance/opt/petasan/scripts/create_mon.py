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
import sys
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.common.cmd import call_cmd


cluster_name = configuration().get_cluster_name()
ceph_mon_keyring = ConfigAPI().get_ceph_mon_keyring(cluster_name)
ceph_client_admin_keyring = ConfigAPI().get_ceph_keyring_path(cluster_name)



try:


    cluster_conf = configuration()
    current_node_info=cluster_conf.get_node_info()
    current_node_name = current_node_info.name
    current_cluster_info = cluster_conf.get_cluster_info()
    config_api = ConfigAPI()

    os.makedirs("/var/lib/ceph/mon/{}-{}".format(cluster_name,current_node_name))

    os.makedirs("/tmp/{}".format(current_node_name))

    if not call_cmd("ceph --cluster {} auth get mon. -o /tmp/{}/monkeyring".format(cluster_name,current_node_name)):
        raise Exception("Error executing ceph auth get mon. -o /tmp/{}/monkeyring".format(current_node_name))
    elif not call_cmd("ceph --cluster {} mon getmap -o /tmp/{}/monmap".format(cluster_name,current_node_name)) :
        raise Exception("Error executing ceph mon getmap -o /tmp/{}/monmap".format(current_node_name))
    elif not call_cmd("ceph-mon --cluster {cluster} -i {node_name} --mkfs --monmap /tmp/{node_name}/monmap --keyring /tmp/{node_name}/monkeyring".format(cluster=cluster_name,node_name=current_node_name)):
        raise Exception("Error executing ceph-mon -i {node_name} --mkfs --monmap /tmp/{node_name}/monmap --keyring /tmp/{node_name}/monkeyring".format(node_name=current_node_name))

    open("/var/lib/ceph/mon/{}-{}/done".format(cluster_name,current_node_name),'w+').close()
    open("/var/lib/ceph/mon/{}-{}/systemd".format(cluster_name,current_node_name),'w+').close()

    call_cmd("chown -R ceph:ceph /var/lib/ceph/mon")

    call_cmd("systemctl enable ceph.target ")
    call_cmd("systemctl enable ceph-mon.target ")
    call_cmd("systemctl enable ceph-mon@{} ".format(current_node_name))
    if not call_cmd("systemctl start ceph-mon@{} ".format(current_node_name)) :
        raise Exception("Error executing  systemctl start ceph-mon@{} ".format(current_node_name))

    call_cmd("ceph-create-keys --cluster {} -i {}  ".format(cluster_name,current_node_name))
    # create Ceph manager
    call_cmd('/opt/petasan/scripts/create_mgr.py')

    sys.exit(0)
except Exception as ex:

    logger.exception(ex.message)
    sys.exit(-1)
sys.exit(-1)