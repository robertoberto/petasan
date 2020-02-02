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

import subprocess
from time import sleep
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.log import logger
from PetaSAN.core.common.enums import SarOutputProperties
from PetaSAN.core.common.sar import Sar
from PetaSAN.backend.cluster_leader import ClusterLeader
from PetaSAN.core.common.smart import Smart
from PetaSAN.core.common.graphite_sender import GraphiteSender

STATS_INTERVAL = 60
SAMPLE_DURATION = 3

config = configuration()
node_name = config.get_node_name()
leader_ip = None

counter = 0


graphite_sender = GraphiteSender()



def exec_command_ex2(cmd):
    p = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    ret = p.returncode
    return ret, stdout, stderr


def _send_graphite(key, val):
    #cmd = "echo 'PetaSAN.NodeStats.{node}.{key} {val}' `date +%s` |  nc -q0 {server}  2003".\
    cmd = 'echo \"PetaSAN.NodeStats.{node}.{key} {val} `date +%s` \"  |  nc -q0 {server}  2003'.\
        format(node=node_name, key=key, val=val, server=leader_ip)
    logger.debug(cmd)

    ret, stdout, stderr = exec_command_ex2(cmd)  #use this function to check stderr
    if stderr is not None and len(stderr) > 0:
        raise Exception("Error running echo command :" + cmd)
   
def get_stats():
    sar_result = Sar(False).run(SAMPLE_DURATION)
    _get_cpu(sar_result)
    _get_ram(sar_result)
    _get_network(sar_result)
    _get_disk(sar_result)
    graphite_sender.send(leader_ip)


def get_smart_stats():
    base_key = "disks.smart."
    smart_attributes = Smart().get_attributes()
    print(smart_attributes)
    for disk_name, attribute in smart_attributes.items():
        for attribute_name in attribute:
            path_key = base_key + disk_name + "." + attribute_name
            val = attribute[attribute_name]
            #_send_graphite(path_key, val)
            graphite_sender.add(path_key, val)


def _get_cpu(sar_result):
    val = sar_result.cpu_avg
    path_key = "cpu_all.percent_util"
    #_send_graphite(path_key, val)
    graphite_sender.add(path_key, val)


def _get_ram(sar_result):
    val = sar_result.ram.__dict__[SarOutputProperties.ram_memused]
    path_key = "memory.percent_util"
    #_send_graphite(path_key, val)
    graphite_sender.add(path_key, val)


def _get_disk(sar_result):
    for disk in sar_result.disks:
        path_key = "disks.percent_util.{}".format(disk.__dict__[SarOutputProperties.disk_DEV])
        val = float(disk.__dict__[SarOutputProperties.disk_util])
        #_send_graphite(path_key, val)
        graphite_sender.add(path_key, val)

        path_key = "disks.throughput.{}_write".format(disk.__dict__[SarOutputProperties.disk_DEV])
        val = float(disk.__dict__[SarOutputProperties.disk_wkB]) * 1024.00
        #_send_graphite(path_key, val)
        graphite_sender.add(path_key, val)

        path_key = "disks.throughput.{}_read".format(disk.__dict__[SarOutputProperties.disk_DEV])
        val = float(disk.__dict__[SarOutputProperties.disk_rkB]) * 1024.00
        #_send_graphite(path_key, val)
        graphite_sender.add(path_key, val)

        path_key = "disks.iops_all.{}".format(disk.__dict__[SarOutputProperties.disk_DEV])
        val = float(disk.__dict__[SarOutputProperties.disk_tps])
        #_send_graphite(path_key, val)
        graphite_sender.add(path_key, val)
    pass


def _get_network(sar_result):
    for iface in sar_result.ifaces:
        path_key = "ifaces.percent_util.{}".format(iface.__dict__[SarOutputProperties.iface_IFACE])
        val = float(iface.__dict__[SarOutputProperties.iface_ifutil])
        #_send_graphite(path_key, val)
        graphite_sender.add(path_key, val)

        path_key = "ifaces.throughput.{}_received".format(iface.__dict__[SarOutputProperties.iface_IFACE])
        val = float(iface.__dict__[SarOutputProperties.iface_rxkB]) * 1024.00
        #_send_graphite(path_key, val)
        graphite_sender.add(path_key, val)

        path_key = "ifaces.throughput.{}_transmitted".format(iface.__dict__[SarOutputProperties.iface_IFACE])
        val = float(iface.__dict__[SarOutputProperties.iface_txkB]) * 1024.00
        #_send_graphite(path_key, val)
        graphite_sender.add(path_key, val)


def get_leader_ip():

    leader = ClusterLeader().get_leader_node()
    management_nodes = config.get_management_nodes_config()
    for node in management_nodes:
        if node.name == leader:
            ip = node.management_ip
            return ip
    return None


while True:
    try:
        graphite_sender.clear_metrics_list()
        if leader_ip is None or len(leader_ip) == 0:
            leader_ip = get_leader_ip()

        if leader_ip is not None and len(leader_ip) > 0:
            counter = counter + 1


            if counter%10 == 0:
                get_smart_stats()

            get_stats()

    except Exception as e:
        logger.error("Node Stats exception.")
        logger.exception(e.message)
        leader_ip = get_leader_ip()

    sleep(STATS_INTERVAL)




