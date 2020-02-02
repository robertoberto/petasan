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
import datetime


class ReplicationActiveJob(object):
    def __init__(self):

        self.job_id = ""           # example : "{replication_job_id}-{timestamp}" --> "00001-1547563576709" or "00001-2019-01-15 16:46:16"
        self.job_name = ""
        self.node_name = ""
        self.uncompressed_transferred_bytes = ""
        self.uncompressed_transferred_rate = ""
        self.compressed_transferred_bytes = ""
        self.compressed_transferred_rate = ""

        self.compression_ratio = ""
        self.elapsed_time = ""

        self.pid = ""                       # process id --> returned from job manager
        self.progress = ""                  # The number of bytes

        self.start_time = str(datetime.datetime(1, 1, 1, 0, 0 , 0 , 0)).split('.')[0]
               # 2019-01-15 16:46:16  -->  year, month, day, hour, minute , second , microsecond


    def load_json(self, j=""):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=False, indent=4)
        return j




