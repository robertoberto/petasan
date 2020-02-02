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

from PetaSAN.core.ceph.ceph_osd import ceph_down_osds
from PetaSAN.core.common.log import logger
from time import sleep
from PetaSAN.core.common.messages import gettext
from PetaSAN.core.notification.base import CheckBasePlugin, Result


class OSDDownPlugin(CheckBasePlugin):
    def __init__(self, context):
        self.__context = context

    def is_enable(self):
        return True

    def run(self):
        try:
            old_osd_down_list = self.__context.state.get(self.get_plugin_name(), {})
            current_osd_down_list = ceph_down_osds()
            for osd_id, node_name in current_osd_down_list.iteritems():
                if osd_id not in old_osd_down_list.keys():
                    result = Result()
                    result.plugin_name = self.get_plugin_name()
                    result.title = gettext("core_message_notify_osd_down_title")
                    result.message = '\n'.join(gettext("core_message_notify_osd_down_body").split("\\n")).format \
                        (''.join('\n- osd.{}/{} '.format(key, val) for key, val in current_osd_down_list.iteritems()))
                    #logger.warning(result.message)
                    self.__context.results.append(result)
                    break
            self.__context.state[self.get_plugin_name()] = current_osd_down_list

        except Exception as e:
            logger.exception(e)
            logger.error("An error occurred while OSDDownPlugin was running.")

    def get_plugin_name(self):
        return self.__class__.__name__
