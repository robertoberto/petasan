#!/usr/bin/python
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

from PetaSAN.core.common.enums import BondMode
import sys
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.cluster.network import Network
from PetaSAN.core.common.cmd import *

logger.debug("Loading network configurations.")
network = Network()

config = configuration()
node = config.get_node_info()
cluster = config.get_cluster_info()

node_management_eth_name = network.get_node_management_interface()
node_management_vlan_id = network.get_node_management_vlan_id()
node_management_eth_ip = network.get_node_management_ip()
node_management_eth_netmask = network.get_node_management_netmask()

gateway = Network().get_def_gateway()
bonds = config.get_cluster_bonds()
jumbo_eths = []
if hasattr(configuration().get_cluster_info(), "jumbo_frames"):
    jumbo_eths = config.get_cluster_info().jumbo_frames


def create_bond(bond):
    if call_cmd("echo +{} >  /sys/class/net/bonding_masters".format(bond.name)):
        # logger.debug("echo +{} >  /sys/class/net/bonding_masters".format(bond.name))
        if call_cmd("echo {} > /sys/class/net/{}/bonding/mode".format(bond.mode, bond.name)):
            # logger.debug("echo {} > /sys/class/net/{}/bonding/mode".format(bond.mode, bond.name))
            if call_cmd("echo 100 > /sys/class/net/{}/bonding/miimon".format(bond.name)):
                # logger.debug("echo 100 > /sys/class/net/{}/bonding/miimon".format(bond.name))
                if BondMode.active_backup == bond.mode or BondMode.balance_alb == bond.mode or BondMode.balance_tlb == bond.mode:

                    if not call_cmd(
                            "echo {} > /sys/class/net/{}/bonding/primary".format(bond.primary_interface, bond.name)):
                        network.clean_bonding()
                        return False

                if BondMode.mode_802_3_ad == bond.mode:
                    if not call_cmd("echo layer2+3 > /sys/class/net/{}/bonding/xmit_hash_policy".format(bond.name)):
                        network.clean_bonding()
                        return False

                for eth in bond.interfaces.split(','):
                    call_cmd("ip address flush dev {eth} ".format(eth=eth))
                    call_cmd("ifconfig {eth} down ".format(eth=eth))
                    if not call_cmd("echo +{}> /sys/class/net/{}/bonding/slaves".format(eth, bond.name)):
                        network.clean_bonding()
                        return False
                if call_cmd("ifconfig {} up ".format(bond.name)):
                    return True
    network.clean_bonding()
    return False


def clean_interfaces():
    call_cmd("route del default")

    # clear ips
    for eth in network.get_node_interfaces(True):
        call_cmd("ip address flush dev {eth} ".format(eth=eth.name))
        call_cmd("ip link set {eth} mtu 1500".format(eth=eth.name))

    # delete vlan interfaces
    for eth in network.get_node_interfaces(True):
        if '.' in eth.name:
            call_cmd("ip link del {eth} ".format(eth=eth.name))

    for eth in network.get_none_bond_interfaces():
        call_cmd("ifconfig {eth} up ".format(eth=eth.name))


def set_ips():
    # -------------- Set IP for management --------------#
    # ================================================== #
    management_eth = node_management_eth_name

    if node_management_vlan_id is not None and len(node_management_vlan_id) > 0:
        management_eth = management_eth + '.' + node_management_vlan_id

    if not call_cmd("ip address add {}/{} dev {}".format(node_management_eth_ip, node_management_eth_netmask,
                                                         management_eth)):
        logger.error("Error setting node ips.")
        return False

    # --------------  Set IP for backend1  -------------- #
    # =================================================== #
    backend_1_eth = cluster.backend_1_eth_name

    if cluster.backend_1_vlan_id is not None and len(cluster.backend_1_vlan_id) > 0:
        backend_1_eth = backend_1_eth + '.' + cluster.backend_1_vlan_id

    if not call_cmd("ip address add {}/{} dev {}".format(node.backend_1_ip, cluster.backend_1_mask,
                                                         backend_1_eth)):
        logger.error("Error setting node ips.")
        return False

    # --------------  Set IP for backend2  -------------- #
    # =================================================== #
    backend_2_eth = cluster.backend_2_eth_name

    if cluster.backend_2_vlan_id is not None and len(cluster.backend_2_vlan_id) > 0:
        backend_2_eth = backend_2_eth + '.' + cluster.backend_2_vlan_id

    if not call_cmd("ip address add {}/{} dev {}".format(node.backend_2_ip, cluster.backend_2_mask,
                                                         backend_2_eth)):
        logger.error("Error setting node ips.")
        return False

    if gateway is not None and not call_cmd(
            "route add default gw {} {}".format(gateway, management_eth)):
        logger.error("Error setting default gateway")
        return False

    return True


def set_vlan():
    # -------------- Set VLAN for management -------------- #
    # ===================================================== #
    if node_management_vlan_id is not None and len(node_management_vlan_id) > 0:
        management_eth = node_management_eth_name + '.' + node_management_vlan_id
        if not call_cmd("ip link add link {} name {} type vlan id {}".format(node_management_eth_name, management_eth,
                                                                             node_management_vlan_id)):
            logger.error("Error setting management vlan.")
            return False

        if not call_cmd("ip link set dev {} up".format(management_eth)):
            logger.error("Error setting management vlan.")
            return False

    # -------------- Set VLAN for backend1 -------------- #
    # =================================================== #
    if cluster.backend_1_vlan_id is not None and len(cluster.backend_1_vlan_id) > 0:
        backend_1_eth = cluster.backend_1_eth_name + '.' + cluster.backend_1_vlan_id
        if not call_cmd("ip link add link {} name {} type vlan id {}".format(cluster.backend_1_eth_name, backend_1_eth,
                                                                             cluster.backend_1_vlan_id)):
            logger.error("Error setting backend1 vlan.")
            return False

        if not call_cmd("ip link set dev {} up".format(backend_1_eth)):
            logger.error("Error setting backend1 vlan.")
            return False

    # -------------- Set VLAN for backend2 -------------- #
    # =================================================== #
    if cluster.backend_2_vlan_id is not None and len(cluster.backend_2_vlan_id) > 0:
        backend_2_eth = cluster.backend_2_eth_name + '.' + cluster.backend_2_vlan_id
        if not call_cmd("ip link add link {} name {} type vlan id {}".format(cluster.backend_2_eth_name, backend_2_eth,
                                                                             cluster.backend_2_vlan_id)):
            logger.error("Error setting backend2 vlan.")
            return False

        if not call_cmd("ip link set dev {} up".format(backend_2_eth)):
            logger.error("Error setting backend2 vlan.")
            return False

    return True


def set_jumbo_frames(bonds, eths):
    for eth in eths:
        if not call_cmd("ip link set {eth} mtu 9000 ".format(eth=eth)):
            logger.error("Error setting interface jumbo frames.")
            return False

    for bond in bonds:
        if bond.is_jumbo_frames:
            if not call_cmd("ip link set {eth} mtu 9000 ".format(eth=bond.name)):
                logger.error("Error setting bond jumbo frames.")
                return False
    return True


# end method

logger.debug("Cleaning bonding.")
if not network.clean_bonding():
    logger.error("Error cleaning bonding.")
    sys.exit(-1)
logger.debug("Cleaning interfaces.")
clean_interfaces()

logger.debug("Creating bond.")
for bond in bonds:
    if not create_bond(bond):
        logger.error("Error creating bond {}.".format(bond.name))
        sys.exit(-1)

logger.debug("Setting jumbo frames.")
if not set_jumbo_frames(bonds, jumbo_eths):
    sys.exit(-1)

logger.debug("Setting VLANs.")
if not set_vlan():
    logger.error("Error setting vlans")
    sys.exit(-1)

logger.debug("Setting IPs.")
if not set_ips():
    logger.error("Error setting node ips")
    sys.exit(-1)

sys.exit(0)

