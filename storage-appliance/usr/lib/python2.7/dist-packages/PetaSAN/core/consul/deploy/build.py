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

import json
from time import sleep

from PetaSAN.core.consul.ps_consul import Consul

from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.log import logger
from PetaSAN.core.ssh.ssh import ssh
from PetaSAN.core.entity.cluster import NodeInfo
import PetaSAN.core.common.cmd
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.status import StatusReport




def __init__():
    pass


cluster_name = ''

base_conf = '/opt/petasan/config'
consul_conf =  base_conf + '/etc/consul.d'
consul_server_conf = consul_conf + '/server'
consul_client_conf = consul_conf + '/client'
data_dir = base_conf + '/var/consul'


def build_consul():
    try:
        # Generate a Security Key
        keygen = PetaSAN.core.common.cmd.exec_command('consul keygen')[0]
        keygen = str(keygen).splitlines()[0]
        logger.debug('keygen: ' + keygen)

        conf = configuration()
        cluster_info = conf.get_cluster_info()
        cluster_name = cluster_info.name
        logger.info('cluster_name: ' + cluster_name)

        local_node_info = conf.get_node_info()
        logger.info("local_node_info.name: " + local_node_info.name)

        __create_leader_conf_locally(keygen)
        continue_building_cluster = __create_leader_conf_remotely(keygen, cluster_info, local_node_info)

        if continue_building_cluster is True:
            __start_leader_remotely(cluster_info, local_node_info)
            __start_leader_locally()
        else:
            logger.error('Error building Consul cluster')
            consul_status_report = StatusReport()
            consul_status_report.success = False
            consul_status_report.failed_tasks.append('core_consul_deploy_build_error_build_consul_cluster')
            return consul_status_report

        # sleep(5)
        consul_status_report = __test_leaders()
        logger.debug(consul_status_report)
        return consul_status_report
    except Exception as ex:
        logger.exception(ex.message)
        consul_status_report = StatusReport()
        consul_status_report.success = False
        consul_status_report.failed_tasks.append('core_consul_deploy_build_error_build_consul_cluster')
        return consul_status_report


def __create_leader_conf_locally(key_gen):
    PetaSAN.core.common.cmd.exec_command('python ' + ConfigAPI().get_consul_create_conf_script() +
                                         ' -key="' + key_gen + '"')
    return


def __create_leader_conf_remotely(key_gen, cluster_info, local_node_info):
    ssh_exec = ssh()
    for cluster_node in cluster_info.management_nodes:
        remote_node_info = NodeInfo()
        remote_node_info.load_json(json.dumps(cluster_node))
        if local_node_info.backend_1_ip != remote_node_info.backend_1_ip:
            command_result = ssh_exec.call_command(remote_node_info.backend_1_ip,
                                                   'python ' + ConfigAPI().get_consul_create_conf_script() +
                                                   ' -key="' + key_gen + '"')
            if command_result is False:
                logger.error("Could not create Consul Configuration on node: " + remote_node_info.backend_1_ip)
                return command_result
    return True


def __start_leader_locally():
    PetaSAN.core.common.cmd.call_cmd('python ' +
                                     ConfigAPI().get_consul_start_up_script_path())
    return


def __start_leader_remotely(cluster_info, local_node_info):
    logger.info('Start consul leaders remotely.')
    ssh_exec = ssh()
    for cluster_node in cluster_info.management_nodes:
        remote_node_info = NodeInfo()
        remote_node_info.load_json(json.dumps(cluster_node))

        logger.debug('local_node_info.backend_1_ip: ' + local_node_info.backend_1_ip)
        logger.debug('remote_node_info.backend_1_ip: ' + remote_node_info.backend_1_ip)

        if local_node_info.backend_1_ip != remote_node_info.backend_1_ip:
            logger.debug('Sending: ' + 'python ' +
                        ConfigAPI().get_consul_start_up_script_path()
                        + ' -retry-join {} '.format(local_node_info.backend_1_ip))

            ssh_exec.exec_command(remote_node_info.backend_1_ip, 'python ' +
                                  ConfigAPI().get_consul_start_up_script_path()
                                  + ' -retry-join {} '.format(local_node_info.backend_1_ip))
    return


def _leader_status_check_(host):
    con = Consul()
    members = con.agent.members()
    if members is not None:
        for leader in members:
            if leader['Status'] == 1:
                if leader['Name'] == host:
                    return True
    return False


def __test_leaders():
    sleeps = [15, 15, 10, 10, 5, 5]
    tries = 5

    leaders_in_cluster = []
    cluster_members = []

    cluster_conf = configuration()
    current_cluster_info = cluster_conf.get_cluster_info()

    current_node_info = cluster_conf.get_node_info()
    cluster_members.append(current_node_info.name)

    for i in current_cluster_info.management_nodes:
        node_info = NodeInfo()
        node_info.load_json(json.dumps(i))
        cluster_members.append(node_info.name)

    status_report = StatusReport()

    for host in cluster_members:
        while tries:
            status = None
            try:
                status = _leader_status_check_(host)
            except Exception as exc:
                logger.error("Error Connecting to consul for leader check.")
            # if not has_reached_quorum:
            if not status:
                tries -= 1
                sleep_seconds = sleeps.pop()
                logger.warning('waiting %s seconds before retrying', sleep_seconds)
                # time.sleep(sleep_seconds)
                sleep(sleep_seconds)
                status_report.success = False
            else:
                leaders_in_cluster.append(host)
                logger.info('Cluster Node {} joined the cluster and is alive' + host)
                status_report.success = True
                break
        if status_report.success is False:
            status_report.failed_tasks.append('core_consul_deploy_build_node_fail_join_cluster_not_alive'+ "%" +str (host))
    if leaders_in_cluster == cluster_members:
        logger.info("Consul leaders are ready")
        status_report.success = True
        return status_report

    else:
        logger.error("Consul leaders are not ready")
        return status_report


def clean_consul():
    clean_consul_local()
    clean_consul_remote()


def clean_consul_local():
    logger.info("Trying to clean Consul on local node")
    PetaSAN.core.common.cmd.call_cmd('python ' +
                                     ConfigAPI().get_consul_stop_script_path())
    PetaSAN.core.common.cmd.call_cmd('python ' +
                                     ConfigAPI().get_consul_clean_script_path())


def clean_consul_remote():
    conf = configuration()
    ssh_exec = ssh()
    for ip in conf.get_remote_ips(conf.get_node_name()):
        logger.info("Trying to clean Consul on {}".format(ip))
        ssh_exec.call_command(ip, 'python ' +
                              ConfigAPI().get_consul_stop_script_path())
        ssh_exec.call_command(ip, 'python ' +
                              ConfigAPI().get_consul_clean_script_path())


def create_consul_client_config():
    conf = configuration()

    local_node_info = conf.get_node_info()
    command_result = PetaSAN.core.common.cmd.call_cmd(
        'python ' + ConfigAPI().get_consul_create_conf_script()+' -server=False')

    if command_result is False:
        logger.error("Could not create Consul Client Configuration on local node: " + local_node_info.backend_1_ip)
        return command_result
    return True


def start_client():
    logger.info('Start consul client.')
    # ssh_exec = ssh()
    command_result = PetaSAN.core.common.cmd.call_cmd('python ' +
                                                      ConfigAPI().get_consul_client_start_up_script_path())
    return command_result

def build_consul_client():
    status_report = StatusReport()
    status_report.success=False
    if create_consul_client_config():
        if start_client():
            status_report.success=True
            return status_report
        else:
            status_report.failed_tasks.append('core_consul_deploy_build_cluster_node_failed_start_cluster' )
    else:
        status_report.failed_tasks.append('core_consul_deploy_build_cluster_node_not_alive_cant_create_conf_file' )

    return status_report

def replace_consul_leader():
    key_gen=get_security_key_()
    if key_gen is None:
        status_report = StatusReport()
        status_report.failed_tasks.append("core_consul_deploy_build_get_security_key_replace_consul_node")
        return status_report
    PetaSAN.core.common.cmd.exec_command('python ' + ConfigAPI().get_consul_create_conf_script() +
                                         ' -key="' + key_gen + '"')
    __start_leader_locally()
    return __test_leaders()

def get_security_key_():
    # get the security code from the server we're connecting to
    ssh_exec = ssh()

    conf = configuration()
    cluster_info = conf.get_cluster_info()

    for cluster_node in cluster_info.management_nodes:
        remote_node_info = NodeInfo()
        remote_node_info.load_json(json.dumps(cluster_node))
        if remote_node_info.management_ip == conf.get_node_info().management_ip:
            continue
        command_result, err = ssh_exec.exec_command(remote_node_info.management_ip,
                                                    'python ' + ConfigAPI().get_consul_encryption_key_script())

        if err is not None and str(err) != "":
            logger.error("Could not read Consul encryption key from node: " + remote_node_info.management_ip)
            logger.error(err)
            print('command_result: ', command_result)
        else:
            key = str(command_result.splitlines()[0])
            if key is not None and key != "":
                return key
    return None


