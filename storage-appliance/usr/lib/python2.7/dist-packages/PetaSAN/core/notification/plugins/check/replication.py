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
from PetaSAN.core.common.log import logger
from PetaSAN.core.consul.api import ConsulAPI


class Replication(CheckBasePlugin):

    def __init__(self, context):
        self.__context = context



    def is_enable(self):
        return True


    def run(self):
        try:
            status = False
            consul = ConsulAPI()
            failed_jobs = consul.get_replication_failed_jobs()
            if len(failed_jobs) > 0:
                failed_jobs_str = ""
                for job_id, job_info in failed_jobs.iteritems():
                    failed_jobs_str += "\n job id: " + job_id + " job name: " + job_info.job_name
                    status = consul.delete_failed_job(job_id)
                result = Result()
                result.plugin_name = self.get_plugin_name()
                result.title = gettext("core_message_notify_failed_jobs_title")
                result.message = '\n'.join(gettext("core_message_notify_failed_jobs_body").split("\\n")).format(failed_jobs_str)
                self.__context.results.append(result)
                logger.info(result.message)
                logger.info("status of deleting failed jobs from consul is " + str(status))
        except Exception as e:
            logger.exception(e)
            logger.error("An error occurred while ReplicationNotificationPlugin was running.")



    def get_plugin_name(self):
        return self.__class__.__name__

