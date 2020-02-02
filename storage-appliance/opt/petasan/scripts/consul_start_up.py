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


from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.cmd import *
from PetaSAN.core.entity.cluster import NodeInfo
import json
import argparse
from PetaSAN.core.common.log import logger
from PetaSAN.core.common.cmd import exec_command_ex, call_cmd

MAX_OPEN_FILES = 102400

parser = argparse.ArgumentParser(description='This is a script that will start up the configured consul cluster.')
parser.add_argument('-retry-join', '--retry-join', help='', required=False)
args = parser.parse_args()

retry_join_arg = args.retry_join
# print('args.retry_join: ', retry_join_arg)

config = configuration()
node = config.get_node_info()
cluster_info = config.get_cluster_info()


retry_join = ''

for cluster_node in cluster_info.management_nodes:
    remote_node_info = NodeInfo()
    remote_node_info.load_json(json.dumps(cluster_node))

    if remote_node_info.backend_1_ip != node.backend_1_ip:
        retry_join = retry_join + ' -retry-join ' + remote_node_info.backend_1_ip

str_start_command = "consul agent -raft-protocol 2 -config-dir /opt/petasan/config/etc/consul.d/server -bind {} ".format(node.backend_1_ip) + retry_join
# print('A: ', str_start_command)

if retry_join_arg is not None:
    # if str(retry_join).find(str(retry_join_arg)) == -1:
    # print('str_start_command: str_start_command: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', str_start_command)
    str_start_command = str_start_command + " -retry-join " + retry_join_arg

logger.info('str_start_command: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ' + str_start_command)

str_start_command = str(str_start_command).replace('-retry-join ' + node.backend_1_ip, '') + ' >/dev/null 2>&1 &'

print('=======================================================================================')
print("@@@@@@ THE SENT COMMAND: " + str_start_command)
print('=======================================================================================')

subprocess.Popen(str_start_command, shell=True)

# Increase max open files for Consul process :
# ============================================
pid_cmd = "ps aux | grep consul | grep agent"
ret, stdout, stderr = exec_command_ex(pid_cmd)

line_1 = stdout.splitlines()[0]
pid = line_1.split()[1]

ulimit_cmd = "prlimit -n" + str(MAX_OPEN_FILES) + " -p " + pid
call_cmd(ulimit_cmd)

