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

from PetaSAN.core.common import email_utils
from PetaSAN.core.security.api import UserAPI
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.notification.base import NotifyBasePlugin
import smtplib


class EmailNotificationPlugin(NotifyBasePlugin):
    def __init__(self, context):
        self.__context = context

    def is_enable(self):
        pass

    def notify(self):
        try:
            messages = self.__context.state.get(self.get_plugin_name(), None)
            if not messages:
                messages = []
            config_api = ConfigAPI()
            smtp_config = config_api.read_app_config()
            if smtp_config.email_notify_smtp_server == "" and smtp_config.email_notify_smtp_email == "":
                # logger.warning("SMTP configuration not set.")
                return

            followers = self._get_followers()
            for result in self.__context.results:
                if hasattr(result, "is_email_process") and result.is_email_process:
                    continue
                for user in followers:
                    fromaddr = smtp_config.email_notify_smtp_email
                    toaddr = user.email
                    # msg = MIMEMultipart()
                    msg = email_utils.create_msg(fromaddr, toaddr, result.title, result.message)

                    msg.smtp_server = smtp_config.email_notify_smtp_server
                    msg.smtp_server_port = smtp_config.email_notify_smtp_port
                    msg.email_password = smtp_config.email_notify_smtp_password
                    msg.retry_counter = 0
                    msg.full_msg = result.title + "\n" + result.message
                    msg.security = smtp_config.email_notify_smtp_security
                    messages.append(msg)

                result.is_email_process = True
                result.count_of_notify_plugins += 1

            unsent_messages = []
            for msg in messages:
                # Note: any error log and continua
                # Note: if pass remove message from messages

                status = email_utils.send_email(msg.smtp_server, msg.smtp_server_port, msg, msg.email_password,
                                                msg.security)
                if not status.success:
                    msg.retry_counter += 1
                    if msg.retry_counter < 1440:
                        unsent_messages.append(msg)
                    if msg.retry_counter in (1, 120, 480, 960, 1440):
                        logger.error("PetaSAN tried to send this email {} times, Can't send this message: {}.".format(
                            msg.retry_counter, msg.full_msg))
                        logger.exception(status.exception)

            self.__context.state[self.get_plugin_name()] = unsent_messages
        except Exception as ex:
            logger.exception(ex)

    def _get_supported_plugins(self):
        return []

    def _get_followers(self):
        user_list = UserAPI().get_users()
        followers = []
        for usr in user_list:
            if usr.notfiy:
                followers.append(usr)

        return followers

    def get_plugin_name(self):
        return self.__class__.__name__

