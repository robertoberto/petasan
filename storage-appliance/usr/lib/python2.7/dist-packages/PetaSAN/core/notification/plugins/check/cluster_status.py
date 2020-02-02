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
from PetaSAN.core.notification.base import CheckBasePlugin, Result
from PetaSAN.core.common.messages import gettext


class ClusterStatusPlugin(CheckBasePlugin):
    def __init__(self, context):
        self.__context = context

    def is_enable(self):
        return True

    def run(self):
        try:
            result = Result()
            ceph_status_overall = ""

            ceph_api = CephAPI()
            cluster_status = ceph_api.get_ceph_cluster_status()                       # ceph status --format json-pretty

            if cluster_status is not None:
                cluster_status = json.loads(cluster_status)

                # Ceph 12 :
                if "overall_status" in cluster_status["health"] and cluster_status["health"]["overall_status"] is not None:
                    ceph_status_overall = cluster_status["health"]["overall_status"]
                else:
                    ceph_status_overall = cluster_status["health"]["status"]

                if ceph_status_overall == "HEALTH_ERR":
                    prv_err  = self.__context.state.get(self.get_plugin_name(), False)

                    if not prv_err:
                        ceph_health_obj = cluster_status["health"]
                        summary_messages = ""
                        summary_messages_ls = []

                        if "checks" in ceph_health_obj:
                            for key in ceph_health_obj["checks"]:
                                if ceph_health_obj["checks"][key] is not None:
                                    msg = ceph_health_obj["checks"][key]["summary"]["message"]
                                    summary_messages_ls.append(msg)

                        summary_messages = '\n    '.join(summary_messages_ls)

                        result.title = gettext("core_message_notify_cluster_status_title")
                        result.message = '\n'.join(gettext("core_message_notify_cluster_status_body").split("\\n")).format(summary_messages)

                        result.plugin_name = str(self.get_plugin_name())
                        self.__context.results.append(result)
                        self.__context.state[self.get_plugin_name()] = True
                        logger.warning("Cluster overall health status is HEALTH_ERR")

                    return

                self.__context.state[self.get_plugin_name()] = False

        except Exception as e:
            logger.exception(e)
            logger.error("An error occurred while ClusterStatusPlugin was running.")


    def get_plugin_name(self):
        return self.__class__.__name__
