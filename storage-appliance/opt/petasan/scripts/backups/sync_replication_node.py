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


from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.common.cmd import *
from time import sleep
from PetaSAN.core.common.log import logger
from PetaSAN.core.cluster.configuration import configuration

conf_api = ConfigAPI()
cron_script = conf_api.get_cron_script_path()
cron_script = cron_script + " build"
users_script = conf_api.get_replication_sync_users_script_path()
sleep_interval = 30

node_info = configuration().get_node_info()
if not node_info.is_backup:
    logger.error('sync_replication_node called on non-backup node')
    exit(-1)

logger.info('sync_replication_node starting')

while True:

    if call_cmd(cron_script):
        logger.info('syncing cron ok')
        break
    logger.error('error syncing cron, will retry..')
    sleep(sleep_interval)

while True:
    if call_cmd(users_script):
        logger.info('syncing replication users ok')
        break
    logger.error('error syncing replication users, will retry..')
    sleep(sleep_interval)

logger.info('sync_replication_node completed')
exit(0)

