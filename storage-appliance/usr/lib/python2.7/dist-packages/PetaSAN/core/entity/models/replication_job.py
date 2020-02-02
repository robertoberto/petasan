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


class ReplicationJob(object):
    def __init__(self):

        self.job_id = ""                              # NEXT_JOB_ID-SerialNo --> example : "00001"
        self.job_name = ""
        self.node_name = ""
        self.source_cluster_fsid = 0                  # file system id of source cluster
        self.source_cluster_name = ""
        self.source_disk_id = ""
        self.compression_algorithm = ""
        self.destination_cluster_name = ""
        self.destination_disk_id = ""
        self.pre_snap_url = ""                        # What to run before taking snapshot
        self.post_snap_url = ""                       # What to run after taking snapshot
        self.post_job_complete = ""                   # What to run after replication job completed
        self.schedule = {}
        self.status = ""                              # started - stopped



    def load_json(self, j=""):
        self.__dict__ = json.loads(j)

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=False, indent=4)
        return j