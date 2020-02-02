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

from crontab import CronTab
#from Cron.crontab import CronTab

import os
from consul import Consul


from PetaSAN.core.entity.kv import KV
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.models.replication_job import ReplicationJob
from PetaSAN.core.common.log import logger
import shutil
import json


class CronManager(object):
    def __init__(self, node):
        self.node_name = node
        self.tmp_file = "/opt/petasan/tmp/petasan-replication"
        self.dest_file = "/etc/cron.d/petasan-replication"

    def add_comment(self, comment):
        f = open(self.tmp_file, "a")
        f.write("PATH=/sbin:/usr/sbin:/bin:/usr/bin\n")
        f.write(comment + "\n")
        f.close()

    def add_job(self, schedule, script_cmd):


        system_cron = CronTab(tabfile=self.tmp_file, user=False)
        job = system_cron.new(command=script_cmd, user='root')
        job.minute.on(0)

        if schedule['type'] == 'daily':
            if schedule['at'] == -1:
                if schedule['unit'] == 'hours':
                    job.hour.every(schedule['every'])
                else:
                    job.minute.every(schedule['every'])
            else:
                job.hour.on(schedule['at'])
        elif schedule['type'] == 'weekly':

            for day in schedule['week_days']:
                job.dow.also.on(day)

            job.hour.on(schedule['at'])

        elif schedule['type'] == 'monthly':
            if len(schedule['days']) == 0:
                job.day.during(1, 7)
                job.dow.on(schedule['first_week_day'])
            else:

                for day in schedule['days']:
                    job.day.also.on(day)

            job.hour.on(schedule['at'])

        system_cron.write()

    def build_crontab(self):
        directory_path = "/opt/petasan/tmp/"
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        replication = ReplicationCronTab(self.node_name)
        replication.generate_jobs("#Replication Jobs")
        try:
            shutil.move(self.tmp_file, self.dest_file)
        except Exception as e:
            logger.error("Can't generate Cron file")
            logger.exception(e.message)


class ReplicationCronTab(CronManager):
    def __init__(self, node):
        super(ReplicationCronTab, self).__init__(node)
        # CronManager.__init__(self,node)

    def generate_jobs(self, comment):

        self.add_comment(comment)
        jobs_list = {}
        config_api = ConfigAPI()
        job_path = config_api.get_consul_replication_jobs_path()
        consul = Consul()
        kv = KV()
        key, jobs_info = consul.kv.get(job_path, recurse=True)

        if jobs_info and len(jobs_info) > 0:
            for i in jobs_info:
                kv = KV()
                kv.load_json(json.dumps(i))
                replication_job = ReplicationJob()
                replication_job.load_json(kv.Value)
                node = replication_job.node_name
                status = replication_job.status
                if node == self.node_name and status == 'started':
                    jobs_list.update({replication_job.job_id: replication_job})

            for job_id, job_info in jobs_list.iteritems():
                print(job_id)
                cmd = "/opt/petasan/scripts/backups/replication.py run-replication-job --job_id " + str(job_info.job_id)
                self.add_job(job_info.schedule, cmd)
