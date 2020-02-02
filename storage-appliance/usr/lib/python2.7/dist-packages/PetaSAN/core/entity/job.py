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


class JobType:
    ADDDISK = "adddisk"
    DELETEOSD = "deleteosd"
    CLIENTSTRESS = "client_stress"
    STORAGELOAD = "storage_load"
    BENCHMANAGER = "bench_manager"
    ADDJOURNAL = "addjournal"
    DELETEJOURNAL = "deletejournal"
    DELETE_POOL = 'delete_pool'
    DELETE_DISK = 'delete_disk'
    ADDCACHE = "addcache"
    DELETECACHE = "deletecache"
    TEST = "test"


job_scripts = {JobType.ADDDISK: "{} {}".format(ConfigAPI().get_admin_manage_node_script(), "add-osd"),
               JobType.DELETEOSD: "{} {}".format(ConfigAPI().get_admin_manage_node_script(), "delete-osd"),
               JobType.CLIENTSTRESS: " {} {}".format(ConfigAPI().get_benchmark_script_path(), "client"),
               JobType.STORAGELOAD: " {} {}".format(ConfigAPI().get_benchmark_script_path(), "storage"),
               JobType.BENCHMANAGER: " {} {}".format(ConfigAPI().get_benchmark_script_path(), "manager"),
               JobType.ADDJOURNAL: "{} {}".format(ConfigAPI().get_admin_manage_node_script(), "add-journal"),
               JobType.DELETEJOURNAL: "{} {}".format(ConfigAPI().get_admin_manage_node_script(), "delete-journal"),
               JobType.DELETE_POOL: ConfigAPI().get_delete_pool_scipt(),
               JobType.DELETE_DISK: ConfigAPI().get_delete_disk_scipt(),
               JobType.ADDCACHE: "{} {}".format(ConfigAPI().get_admin_manage_node_script(), "add-cache"),
               JobType.DELETECACHE: "{} {}".format(ConfigAPI().get_admin_manage_node_script(), "delete-cache"),

               JobType.TEST: '/opt/petasan/scripts/test.sh -arg1 -arg2 '}


class Job(object):
    def __init__(self):
        self.id = -1
        self.type = ""
        self.params = ""
        self.is_running = False
        self.started_since = ""
