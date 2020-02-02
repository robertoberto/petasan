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

from PetaSAN.core.notification.base import Result , CheckBasePlugin
from PetaSAN.core.common.messages import gettext
from PetaSAN.backend.manage_node import ManageNode
from PetaSAN.core.common.log import logger

smart_counter = 0

class SMARTFailurePlugin(CheckBasePlugin):


    def __init__(self , context):
        self.__context = context



    def is_enable(self):
        return True


    def run(self):
        try:
            global smart_counter
            node_failed_disks = []
            differences_nodes_disks_down = {}
            smart_counter += 1
            if smart_counter % 10 == 0:
                old_node_disks_health = self.__context.state.get(self.get_plugin_name() , {})
                current_node_failed_disks = self.__get_failed_disks()

                for node , failed_disks in current_node_failed_disks.iteritems():
                    if node in old_node_disks_health.keys():
                        for failed_disk in failed_disks:
                            if failed_disk not in old_node_disks_health[node]:
                                node_failed_disks.append(failed_disk)
                        if len(node_failed_disks) > 0:
                            differences_nodes_disks_down.update({node : node_failed_disks})
                    else:
                        differences_nodes_disks_down.update({node : failed_disks})



                if len(differences_nodes_disks_down) > 0:

                    new_failures = ''
                    for node , failed_disks in differences_nodes_disks_down.iteritems():
                        new_failures += str("\n  Node : " + node + "   Disk(s) : ")
                        for failed_disk in failed_disks:
                            if failed_disk != failed_disks[-1]:
                                new_failures += str(failed_disk+", ")
                            else:
                                new_failures += str(failed_disk)


                    all_failures = ''
                    for node , failed_disks in current_node_failed_disks.iteritems():
                        all_failures += str("\n  Node : " + node + "  Disk(s) : ")
                        for failed_disk in failed_disks:
                            if failed_disk != failed_disks[-1]:
                                all_failures += str(failed_disk+" , ")
                            else:
                                all_failures += str(failed_disk)





                    result = Result()
                    result.plugin_name = self.get_plugin_name()
                    result.title = gettext("core_message_notify_smart_disk_health_failed_title")
                    result.message = '\n'.join(gettext("core_message_notify_smart_disk_health_failed_body").split("\\n")).format(new_failures , all_failures)
                    self.__context.results.append(result)
                    logger.info(result.message)


                self.__context.state[self.get_plugin_name()] = current_node_failed_disks

        except Exception as e:
            logger.exception(e)
            logger.error("An error occurred while SMARTFailurePlugin was running.")




    def __get_failed_disks(self):

        manage_node = ManageNode()
        failed_disk_list = []
        failed_node_disks = {}
        node_list = manage_node.get_node_list()

        for node in node_list:
            failed_disk_list = []
            if node.status == 1:
                node_disks_health = manage_node.get_disks_health(node.name)

                if len(node_disks_health) >0:

                    for disk , disk_health in node_disks_health.iteritems():
                        if disk_health == 'Failed':
                            failed_disk_list.append(disk)
                    if len(failed_disk_list) > 0:
                        failed_node_disks.update({node.name : failed_disk_list})
                    failed_disk_list = []

        return failed_node_disks




    def get_plugin_name(self):
        return self.__class__.__name__











