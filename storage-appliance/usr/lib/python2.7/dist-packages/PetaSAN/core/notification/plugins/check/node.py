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

from PetaSAN.core.common.enums import NodeStatus
from PetaSAN.core.common.log import logger
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.notification.base import CheckBasePlugin,NotifyContext, Result
from PetaSAN.core.common.messages import gettext

class NodeDownPlugin(CheckBasePlugin):
    def __init__(self,context):
        self.__context = context


    def is_enable(self):
        return True


    def run(self):
        self.__notify_list()

    def get_plugin_name(self):
        return self.__class__.__name__



    def __get_down_node_list(self):
        down_node_list = []
        try:
            con_api = ConsulAPI()
            node_list = con_api.get_node_list()
            consul_members = con_api.get_consul_members()
            for i in node_list:
                if i.name not in consul_members:
                    i.status = NodeStatus.down
                    down_node_list.append(i.name)
            return down_node_list
        except Exception as e:
            logger.exception("error get down node list")
            return down_node_list

    def __notify_list(self):
        try:
            result = Result()
            old_node_list = self.__context.state.get(self.get_plugin_name(),[])
            down_node_list = self.__get_down_node_list()
            for node in down_node_list:
                if node not in old_node_list:
                    result.message= '\n'.join(gettext("core_message_notify_down_node_list").split("\\n")).format(''.join('\n- node:{} '.format(node) for node in down_node_list))
                    #logger.warning(result.message)
                    result.plugin_name=str(self.get_plugin_name())
                    result.title = gettext("core_message_notify_down_node_list_title")
                    self.__context.results.append(result)
                    break
            self.__context.state[self.get_plugin_name()]= down_node_list
        except Exception as e:
            logger.exception("error notify down node list")
