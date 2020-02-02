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

import threading
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.entity.models.replication_active_job import ReplicationActiveJob
import time
import sys
import os
import json
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.common.log import logger
import datetime
import re


class ProgressUpdaterThread(threading.Thread):
    progress_file_path = ""
    uncompressed_file_path = ""
    compresses_file_path = ""
    active_job_id = ""
    progress = {"uncompressed_transferred_bytes": "", "uncompressed_transferred_rate": "", "compressed_transferred_bytes": "", "compressed_transferred_rate": "", "ratio" : "", "percentage" : ""}

    def __init__(self, active_job_id, uncompressed_file_path , compressed_file_path, progress_file_path):
        threading.Thread.__init__(self)
        self.uncompressed_file_path = uncompressed_file_path
        self.compressed_file_path = compressed_file_path
        self.progress_file_path = progress_file_path
        self.active_job_id = active_job_id



    def run(self):
        consul = ConsulAPI()
        job_id = self.active_job_id.split('-')[0]
        active_job = consul.get_replication_active_job(job_id)

        while True:
            if len(self.uncompressed_file_path) > 0 and os.path.exists(self.uncompressed_file_path):
                for i in range(5):
                    try:
                        if os.stat(self.uncompressed_file_path).st_size > 0:
                            with open(self.uncompressed_file_path, 'r') as outfile:
                                uncompressed_data_json = outfile.read()
                                if len(uncompressed_data_json) > 0:
                                    uncompressed_data = json.loads(uncompressed_data_json)

                                    self.progress['uncompressed_transferred_bytes'] = uncompressed_data['transferred_bytes']
                                    self.progress['uncompressed_transferred_rate'] = uncompressed_data['transfer_rate']

                                    active_job.uncompressed_transferred_bytes = self.progress['uncompressed_transferred_bytes']
                                    active_job.uncompressed_transferred_rate = self.progress['uncompressed_transferred_rate']
                                    start_time = datetime.datetime.strptime(active_job.start_time, "%Y-%m-%d %H:%M:%S")
                                    now_string_format = str(datetime.datetime.now()).split('.')[0]
                                    now = datetime.datetime.strptime(now_string_format, "%Y-%m-%d %H:%M:%S")
                                    elapsed_time = now - start_time
                                    active_job.elapsed_time = str(elapsed_time).split(':')[0] + ':' + str(elapsed_time).split(':')[1]
                                    break

                    except Exception as e:
                        logger.error(e)
                        logger.error("Error in open uncompressed progress file")
                        time.sleep(2)
                        continue

            else:
                break

            if len(self.compressed_file_path) > 0 and os.path.exists(self.compressed_file_path):
                for j in range(5):
                    try:
                        if os.stat(self.compressed_file_path).st_size > 0:
                            with open(self.compressed_file_path, 'r') as outfile:
                                compressed_data_json = outfile.read()
                                if len(compressed_data_json) > 0:
                                    compressed_data = json.loads(compressed_data_json)

                                    self.progress['compressed_transferred_bytes'] = compressed_data['transferred_bytes']
                                    self.progress['compressed_transferred_rate'] = compressed_data['transfer_rate']

                                    uncompressed = self.progress['uncompressed_transferred_bytes'].strip()
                                    compressed = self.progress['compressed_transferred_bytes'].strip()

                                    if len(compressed) > 0 and len(uncompressed) > 0:
                                        uncompressed_val = float(re.findall(r'-?\d+\.?\d*', uncompressed)[0])
                                        compressed_val = float(re.findall(r'-?\d+\.?\d*', compressed)[0])

                                        if compressed_val > 0:
                                            self.progress['ratio'] = str(round (uncompressed_val / compressed_val, 2))

                                        active_job.compressed_transferred_bytes = self.progress['compressed_transferred_bytes']
                                        active_job.compressed_transferred_rate = self.progress['compressed_transferred_rate']
                                        active_job.compression_ratio = self.progress["ratio"]

                                        break

                    except Exception as e:
                        logger.error(e)
                        time.sleep(2)
                        continue

            if len(self.progress_file_path) > 0 and os.path.exists(self.progress_file_path):
                for j in range(5):
                    try:

                        if os.stat(self.progress_file_path).st_size > 0:
                            cmd = "tac {} | grep Importing -m 1".format(self.progress_file_path)
                            ret, stdout, stderr = exec_command_ex(cmd)
                            if ret != 0:
                                if stderr:
                                    logger.error(stderr)

                            if stdout and "complete" in stdout:
                                output = stdout.split(':')

                                i = len(output) - 1
                                while i >= 0:
                                    if "complete..." in output[i]:
                                        progress_element = output[i]
                                        self.progress['percentage'] = progress_element.split("complete...")[0].strip()
                                        break
                                    i -= 1

                            active_job.progress = self.progress['percentage']

                            break

                    except Exception as e:
                        logger.error(e)
                        time.sleep(2)
                        continue


            confirm = consul.update_replication_active_job(active_job)
            time.sleep(6)

        return
