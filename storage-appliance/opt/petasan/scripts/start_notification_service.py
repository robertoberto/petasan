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

from PetaSAN.backend.notification_manager import Service
from PetaSAN.core.entity.app_config import AppConfig
from PetaSAN.core.config.api import ConfigAPI


# This method will use to upgrade email configuration from 1.4 to 1.5
def __upgrade_email_config():
    try:
        config_api = ConfigAPI()
        old_config = config_api.read_app_config()
        if hasattr(old_config, "email_notify_smtp_is_ssl"):

            new_config = AppConfig()

            new_config.iqn_base = old_config.iqn_base
            new_config.iscsi1_subnet_mask = old_config.iscsi1_subnet_mask
            new_config.iscsi1_auto_ip_from = old_config.iscsi1_auto_ip_from
            new_config.iscsi1_auto_ip_to = old_config.iscsi1_auto_ip_to
            new_config.iscsi2_subnet_mask = old_config.iscsi2_subnet_mask
            new_config.iscsi2_auto_ip_from = old_config.iscsi2_auto_ip_from
            new_config.iscsi2_auto_ip_to = old_config.iscsi2_auto_ip_to
            new_config.email_notify_smtp_server = old_config.email_notify_smtp_server
            new_config.email_notify_smtp_port = old_config.email_notify_smtp_port
            new_config.email_notify_smtp_email = old_config.email_notify_smtp_email
            new_config.email_notify_smtp_password = old_config.email_notify_smtp_password

            if old_config.email_notify_smtp_is_ssl == False and old_config.email_notify_smtp_server != "":
                new_config.email_notify_smtp_security = 2
            config_api.write_app_config(new_config)
    except:
        pass


__upgrade_email_config()
Service().start()

