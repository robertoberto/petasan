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

from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.common.CustomException import ConsulException
from PetaSAN.core.common.log import logger

from PetaSAN.core.cluster.job_manager import JobManager
from PetaSAN.core.entity.job import JobType



class ManagePools:
    def __init__(self):
        pass

    def get_pools_info(self):
        ceph_api = CephAPI()
        pools_info = ceph_api.get_pools_info()
        return pools_info


    def add_pool(self , poolInfo):
        ceph_api = CephAPI()
        ceph_api.add_pool(poolInfo)


    def update_pool(self , poolInfo):
        ceph_api = CephAPI()
        ceph_api.update_pool(poolInfo)


    def delete_pool(self , pool_name):
        jm = JobManager()
        id = jm.add_job(JobType.DELETE_POOL,pool_name +' --yes-i-really-really-mean-it')
        return id

    def is_pool_deleting(self,id):
        jm = JobManager()
        return jm.is_done(id)

    def get_active_pools(self):
        ceph_api = CephAPI()
        active_pools = ceph_api.get_active_pools()
        return active_pools


    def get_active_replicated_pools(self):
        ceph_api = CephAPI()
        active_pools = ceph_api.get_active_pools()
        pools_info = ceph_api.get_pools_info()
        replicated_active_pools = []
        for pool in pools_info:
            if pool.type == 'replicated' and pool.name in active_pools:
                replicated_active_pools.append(pool.name)
        return replicated_active_pools



