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
from PetaSAN.core.common.cmd import exec_command_ex

class GraphiteSender(object):
    MAX_SEND_COUNT = 10

    def __init__(self):
        self.node_name = configuration().get_node_name()
        self.max_limit = self.MAX_SEND_COUNT
        self.metrics_list = []


    def add(self, key, value):
        metric ="\"PetaSAN.NodeStats.{node}.{key} {val}  `date +%s`\" ".\
            format(node=self.node_name, key=key, val=value)

        self.metrics_list.append(metric)


    def send(self, server_ip):
        if server_ip is not None and len(server_ip) > 0:
            while len(self.metrics_list) > 0:
                start_index = 0
                cmd = "echo "

                if len(self.metrics_list) > self.max_limit:
                    end_index = self.max_limit
                else:
                    end_index = len(self.metrics_list)

                metrics_sublist = self.metrics_list[start_index:end_index]

                for metric in metrics_sublist:
                    if metric is not metrics_sublist[0] and metric.startswith("\"PetaSAN."):
                        metric = metric.replace("\"PetaSAN.", "\"\nPetaSAN.")
                    cmd += metric

                cmd += " |  nc -q0 {server_ip}  2003".format(server_ip = server_ip)


                ret, stdout, stderr = exec_command_ex(cmd)
                if stderr is not None and len(stderr) > 0:
                    self.clear_metrics_list()
                    raise Exception("Error running echo command :" + cmd)

                self.metrics_list = self.metrics_list[end_index:]


    def clear_metrics_list(self):
        self.metrics_list = []
