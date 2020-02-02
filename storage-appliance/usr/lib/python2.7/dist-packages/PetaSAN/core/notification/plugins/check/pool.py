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
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.notification.base import CheckBasePlugin, Result
from PetaSAN.core.common.messages import gettext


old_pools = {}

class PoolSizePlugin(CheckBasePlugin):
    def __init__(self, context):
        self.__context = context

    def is_enable(self):
        return True

    def run(self):
        try:
            global old_pools
            current_pools = {}
            pools_used_space = {}
            notify_pool_size = ConfigAPI().get_notify_pool_used_space_percent()

            ## Getting the notional percentage of storage used for each pool ##
            ## ------------------------------------------------------------- ##
            pools_used_space = self.get_pools_used_space()

            ## Loop and do checks for each pool ##
            ## -------------------------------- ##
            for pool_name, pool_space in pools_used_space.iteritems():
                # Check if pool space is greater than or equal 85% of pool total space or not #
                if pool_space >= notify_pool_size:
                    # Check if the same pool name and the same pool space exist in "old_pools" dictionary #
                    key, value = pool_name, pool_space
                    if key in old_pools and value == old_pools[key]:
                        continue

                    current_pools[pool_name] = pool_space

                # If pool space is less than 85% --> remove pool from "old_pools" dictionary if exists #
                else:
                    if pool_name in old_pools:
                        del old_pools[pool_name]

            ## Notify user if length of "current_pools" > 0 ##
            ## -------------------------------------------- ##
            if len(current_pools) > 0:
                self.__context.state[self.get_plugin_name()] = current_pools
                result = Result()
                result.plugin_name = self.get_plugin_name()
                result.title = gettext("core_message_notify_pool_used_space_title")
                result.message = '\n'.join(gettext("core_message_notify_pool_used_space_body").split("\\n")).format \
                    (''.join('\n - pool : {} , used space = {}%'.format(key, val) for key, val in current_pools.iteritems()))

                # logger.warning(result.message)
                self.__context.results.append(result)

                # Update the dictionary old_pools with the items of the dictionary current_pools #
                old_pools.update(current_pools)

            ## Empty the dictionary current_pools  ##
            ## ----------------------------------- ##
            current_pools = dict()


        except Exception as e:
            logger.exception(e)
            logger.error("An error occurred while PoolSizePlugin was running.")


    def get_pools_used_space(self):
        pools_used_space = {}
        cluster_name = configuration().get_cluster_name()

        cmd = "ceph df --format json-pretty --cluster {}".format(cluster_name)
        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                logger.error("Cannot run cmd : {}".format(cmd))

        stdout_data = json.loads(stdout)

        pools_ls = stdout_data["pools"]

        for pool in pools_ls:
            pool_name = pool["name"]
            pool_stats = pool["stats"]
            pool_used_space = round(float(pool_stats["percent_used"]),1)
            pools_used_space[pool_name] = pool_used_space

        return pools_used_space


    def get_plugin_name(self):
        return self.__class__.__name__