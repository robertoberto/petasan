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

from flask import json
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.notification.base import CheckBasePlugin, Result
from PetaSAN.core.common.messages import gettext


class ClusterStorageSizePlugin(CheckBasePlugin):
    def __init__(self, context):
        self.__context = context

    def is_enable(self):
        return True

    def run(self):
        try:
            result = Result()
            ceph_api = CephAPI()
            cluster_status = ceph_api.get_ceph_cluster_status()
            if cluster_status is not None:
                cluster_status = json.loads(cluster_status)

                available_size = 0
                used_size = 0

                if cluster_status['pgmap']['bytes_total'] > 0:
                    available_size = cluster_status['pgmap']['bytes_avail'] * 100.0 / cluster_status['pgmap']['bytes_total']
                    used_size = cluster_status['pgmap']['bytes_used'] * 100.0 / cluster_status['pgmap']['bytes_total']

                notify_cluster_space_percent = ConfigAPI().get_notify_cluster_used_space_percent()

                if float(used_size) > float(notify_cluster_space_percent):
                    check_state = self.__context.state.get(self.get_plugin_name(), False)

                    if check_state == False:
                        result.title = gettext("core_message_notify_title_cluster_out_space")
                        result.message = '\n'.join(gettext("core_message_notify_cluster_out_space").split("\\n")).format(int(available_size))
                        # logger.warning(result.message)
                        result.plugin_name = str(self.get_plugin_name())
                        self.__context.results.append(result)
                        self.__context.state[self.get_plugin_name()] = True
                        logger.warning("Cluster is running out of disk space")
                    return
                self.__context.state[self.get_plugin_name()] = False

        except:
            logger.exception("Error occur during get cluster state")

    def get_plugin_name(self):
        return self.__class__.__name__
