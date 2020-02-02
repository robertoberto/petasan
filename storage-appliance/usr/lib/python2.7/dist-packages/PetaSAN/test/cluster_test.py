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

from distutils.command.config import config
from PetaSAN.core.entity.cluster import NodeInfo



def test_network():
    from PetaSAN.core.cluster.network import Network
    net = Network()
    for i in net.get_node_interfaces():
        print i.name ,i.mac
    print len(net.get_node_interfaces())


def test_is_valid():
    from PetaSAN.backend.cluster.deploy import Wizard
    config = Wizard()
    print config.is_valid_network_setting()


def test_network_management():
    from PetaSAN.core.cluster.network import Network
    net = Network()
    print net.get_node_management_interface()

#test_network()
#test_network_management()
#test_is_valid()



def test_set_cluter_name():
    from PetaSAN.core.cluster.configuration import configuration
    conf = configuration()

    conf.set_cluster_name("test")


def test_get_cluter_info():
    from PetaSAN.core.cluster.configuration import configuration
    conf = configuration()

    xx =conf.get_cluster_info()
    print xx.name_eth_name,xx.iscsi_1_eth_name


def test_set_cluter_info(test):
    from PetaSAN.core.cluster.configuration import configuration
    conf = configuration()

    xx =conf.get_cluster_info()
    print xx.name,xx.iscsi_1_eth_name,xx.backend_1_eth_name,xx.backend_2_eth_name
    xx.iscsi_1_eth_name="eth0"+test
    xx.iscsi_2_eth_name="eth1"+test
    xx.backend_1_eth_name="eth0"+test
    xx.backend_2_eth_name="eth1"+test
    xx.backend_1_mask="255.255.255.0"
    xx.backend_2_mask="255.255.255.0"
    xx.management_eth_name="eth0"+test
    xx.eth_count=4
    conf.set_cluster_network_info(xx)
    xx =conf.get_cluster_info()
    print xx.name\
        ,xx.iscsi_1_eth_name,xx.iscsi_2_eth_name\
        ,xx.backend_1_eth_name,xx.backend_2_eth_name\
        ,xx.management_eth_name,xx.eth_count


def test_set_Node():
    from PetaSAN.core.cluster.configuration import configuration
    from PetaSAN.backend.cluster.manage_node import ManageNode
    from PetaSAN.backend.cluster.deploy import Wizard
    from PetaSAN.core.cluster.network import Network
    net = Network()
    wizerd = Wizard()
    conf = configuration()

    node =NodeInfo()
    m_node = ManageNode()
    node.backend_1_ip="192.168.130.100"
    node.backend_2_ip="192.168.120.100"
    node.management_ip=net.get_node_management_ip()
    #clu= conf.get_cluster_info()
    #clu.management_nodes.append(node)
    #conf.set_cluster_network_info(clu)
    print wizerd.set_node_info(node)
def test_build():
    from PetaSAN.backend.cluster.deploy import Wizard
    wiz = Wizard()
    wiz.build()
    #print  conf.get_node_info().backend_1_eth_name
    #print m_node.start_node_backend_ips()

def test_create_cluster():
    from PetaSAN.backend.cluster.deploy import Wizard
    wiz = Wizard()
    wiz.create_cluster_info("password","test")
    test_set_cluter_info("")
    test_set_Node()
    test_build()
#test_set_cluter_name()
#test_get_cluter_info()
#test_set_cluter_info("")
#test_set_Node()
#test_build()
test_create_cluster()