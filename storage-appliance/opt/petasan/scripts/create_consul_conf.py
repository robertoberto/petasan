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

import argparse
import os
import sys
import subprocess

from PetaSAN.backend.file_sync_manager import FileSyncManager
from PetaSAN.core.consul.deploy.build import *



parser = argparse.ArgumentParser(description='This is a script that will create the consul folder structure and expected '
                                             'configuration.')
parser.add_argument('-key', '--security_key', help='Security key that should be the same for all cluster members',
                    required=False)
parser.add_argument('-server', '--server',
                    help='The Mode in which the node should operate (default is server, if client'
                         'this parameter should be passed and set to False.)',
                    required=False)
args = parser.parse_args()


# cluster_members = []


def get_security_key():
    # get the security code from the server we're connecting to
    ssh_exec = ssh()

    conf = configuration()
    cluster_info = conf.get_cluster_info()

    for cluster_node in cluster_info.management_nodes:
        remote_node_info = NodeInfo()
        remote_node_info.load_json(json.dumps(cluster_node))

        command_result, err = ssh_exec.exec_command(remote_node_info.management_ip,
                                                    'python ' + ConfigAPI().get_consul_encryption_key_script())

        if err is not None:
            logger.error("Could not read Consul encryption key from node: " + remote_node_info.management_ip)
            logger.error(err)
            return command_result
    return None


def get_cluster_members():
    # get the security code from the server we're connecting to
    cluster_members = []

    conf = configuration()
    cluster_info = conf.get_cluster_info()

    for cluster_node in cluster_info.management_nodes:
        remote_node_info = NodeInfo()
        remote_node_info.load_json(json.dumps(cluster_node))
        cluster_members.append(str(remote_node_info.backend_1_ip))

    logger.info('cluster_members: ' + repr(cluster_members))
    return cluster_members


security_key = args.security_key

is_server = True

if args.server is not None:
    is_server = args.server

if is_server is not True:
    get_security_key()

# consul_server_conf = consul_server_conf
#data_dir = data_dir
#consul_conf_file = consul_server_conf + '/config.json'
consul_conf_file =''
consul_config = ''

# Create the Necessary Directory and System Structure
try:
    if is_server is True:
        #os.makedirs(consul_server_conf)
        subprocess.call('mkdir -p ' + consul_server_conf,shell=True)
        consul_conf_file = consul_server_conf + '/config.json'


        consul_config = '{' \
                        '\n"bootstrap_expect": 3,' \
                        '\n"server": true,' \
                        '\n"datacenter": "PetaSAN",' \
                        '\n"data_dir": "' + data_dir + '",' \
                        '\n"encrypt": "' + security_key + '",' \
                        '\n"log_level": "INFO",' \
                        '\n"enable_syslog": true' \
                        '\n}'

    else:
        #os.makedirs(consul_client_conf)
        subprocess.call('mkdir -p ' + consul_client_conf,shell=True)
        consul_conf_file = consul_client_conf + '/config.json'


        consul_config = '{' \
                        '\n"server": false,' \
                        '\n"datacenter": "PetaSAN",' \
                        '\n"data_dir": "' + data_dir + '",' \
                        '\n"bind_addr" :' '"'+configuration().get_node_info().backend_1_ip+'",\n' \
                        '\n"encrypt": "' + get_security_key().splitlines()[0] + '",' \
                        '\n"log_level": "INFO",' \
                        '\n"enable_syslog": true' \
                        '\n}'



        logger.debug(consul_config)
    #os.makedirs(data_dir)
    subprocess.call('mkdir -p ' + data_dir,shell=True)
except Exception as exc:
    logger.exception(exc.message)
    sys.exit(-1)

logger.debug('consul_config: ' + consul_config)

consul_mgr = FileSyncManager()
consul_mgr.write_file(consul_conf_file, consul_config)

