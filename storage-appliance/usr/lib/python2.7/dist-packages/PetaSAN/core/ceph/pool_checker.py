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

from PetaSAN.core.ceph.ceph_authenticator import CephAuthenticator
from PetaSAN.core.ceph.replication.users import Users
import json
import rados
import threading
from time import time

from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.CustomException import CephException
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.ceph.api import CephAPI


# Creating Threading Class
class PoolCheckerThread(threading.Thread):

    def __init__(self, cluster_name, pool):
        threading.Thread.__init__(self)
        self.cluster_name = cluster_name
        self.pool = pool
        self.active_pgs_num = 0
        self.active_osds_num = 0


    def run(self):
        '''
        This function will be executed when we call the start method of any object in our PoolCheckerThread class
        '''
        # Get which ceph user is using this function & get his keyring file path #
        # ====================================================================== #
        ceph_auth = CephAuthenticator()
        cmd = 'ceph pg ls-by-pool {} --format json-pretty {} --cluster {}'.format(self.pool, ceph_auth.get_authentication_string(), self.cluster_name)
        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr and ('Connection timed out' in stderr or 'error connecting' in stderr):
                logger.error('Error in Ceph Connection cmd:' +cmd)
                raise CephException(CephException.CONNECTION_TIMEOUT,'ConnectionTimeError')

            logger.error('General error in Ceph cmd:' + cmd)
            raise CephException(CephException.GENERAL_EXCEPTION,'GeneralCephException')

        output = stdout
        pgdp = PGDumpParser()
        pgdp.parse(output)

        self.active_pgs_num = pgdp.active_pgs
        self.active_osds_num = pgdp.active_osds

        return


# ######################################################################################################################

class PoolChecker():

    def __init__(self, timeout=5.0):
        self.timeout = timeout

    def get_active_pools(self):
        active_pools = []
        ceph_api = CephAPI()
        cluster = None

        try:
            # Get which ceph user is using this function #
            # ========================================== #
            # users = Users()
            # user_name = users.get_current_system_user().strip()
            # if user_name == "root":
            #     user_name = "admin"
            # # Get ceph user's keyring file path #
            # # ================================= #
            # cluster = rados.Rados(conffile=ConfigAPI().get_ceph_conf_path(cluster_name), conf=dict(keyring=ceph_auth.get_keyring_path()), rados_id=user_name)
            # cluster.connect()

            cluster_name = configuration().get_cluster_name()
            ceph_auth = CephAuthenticator()
            cluster = ceph_api.connect()

            # Get all list of pools:
            pools = cluster.list_pools()
            if not pools or len(pools) == 0 :
                active_pools = []

            # Create a list of threads:
            threads = []
            for pool in pools:
                thread = PoolCheckerThread(cluster_name,pool)
                thread.setDaemon(True)
                thread.start()                                                              # Start running the threads!
                threads.append(thread)

            end_time = time() +  self.timeout
            for thread in threads :
                wait = end_time - time()
                if wait < 0:
                    break
                thread.join(wait)                                         # Wait for a timeout for the threads to finish

            for thread in threads :
                # Get pg_num for current thread pool:
                cmd = 'ceph osd pool get {} pg_num {} --cluster {}'.format(thread.pool, ceph_auth.get_authentication_string(), thread.cluster_name)
                ret, stdout, stderr = exec_command_ex(cmd)

                if ret != 0:
                    if stderr and ('Connection timed out' in stderr or 'error connecting' in stderr):
                        logger.error('Error in Ceph Connection cmd:' +cmd)
                        cluster.shutdown()
                        raise CephException(CephException.CONNECTION_TIMEOUT,'ConnectionTimeError')

                    logger.error('General error in Ceph cmd:' + cmd)
                    cluster.shutdown()
                    raise CephException(CephException.GENERAL_EXCEPTION,'GeneralCephException')

                output = stdout
                output_ls = output.split()
                pool_pg_num = output_ls[1]

                if not thread.is_alive() and thread.active_pgs_num > 0 :
                    if thread.active_pgs_num == int(pool_pg_num):
                        active_pools.append(thread.pool)

            active_pools.sort()

        except Exception as e:
            logger.error("PoolChecker error : " + e.message)

        cluster.shutdown()

        return active_pools


    def get_active_osds(self):
        active_osds = {}

        ceph_api = CephAPI()
        cluster = None

        try:
            cluster_name = configuration().get_cluster_name()

            # cluster = rados.Rados(conffile=ConfigAPI().get_ceph_conf_path(cluster_name), conf=dict(keyring=ConfigAPI().get_ceph_keyring_path(cluster_name)))
            # cluster.connect()

            cluster = ceph_api.connect()

            # Get all list of pools:
            pools = cluster.list_pools()
            if not pools or len(pools) == 0 :
                active_osds = []

            # Create a list of threads:
            threads = []
            for pool in pools:
                thread = PoolCheckerThread(cluster_name,pool)
                thread.setDaemon(True)
                thread.start()                                                              # Start running the threads!
                threads.append(thread)

            end_time = time() +  self.timeout
            for thread in threads :
                wait = end_time - time()
                if wait < 0:
                    break
                thread.join(wait)                                         # Wait for a timeout for the threads to finish

                if not thread.is_alive() and thread.active_osds_num > 0 :
                    active_osds[thread.pool] = thread.active_osds_num
                else:
                    active_osds[thread.pool] = 0

        except Exception as e:
            logger.error("PoolChecker error : " + e.message)

        cluster.shutdown()

        return active_osds

"""
from ctypes import *
pthread = cdll.LoadLibrary("libpthread-2.15.so")
pthread.pthread_cancel(c_ulong(t.ident))

import ctypes as C
LIBPTHREAD = "libpthread.so.0"
_libpthread = C.CDLL(LIBPTHREAD, use_errno=True)
_libpthread.pthread_cancel(C.c_ulong(t.ident))
"""


# ######################################################################################################################

class PGDumpParser():

    def __init__(self):
        self.active_pgs = 0
        self.active_osds = 0
        self.OSD_ID_IGNORE = 2147483647

    def parse(self,output):
        output_pg_ls = json.loads(output)

        # Ceph 12 :
        if isinstance(output_pg_ls, list):
            self.parse_pg_ls(output_pg_ls)

        # Ceph 14 :
        if isinstance(output_pg_ls, dict):
            pg_stats = output_pg_ls["pg_stats"]
            self.parse_pg_ls(pg_stats)

        return


    def parse_pg_ls(self, pg_ls):
        active_pg_counter = 0
        active_osds_ls = []
        pg_error_ls = ['down', 'inactive', 'stale', 'incomplete', 'unfound', 'inconsistent']

        for pg in pg_ls:
            if 'state' in pg:
                pg_state = pg['state']
                pg_state_list = pg_state.split('+')

                if 'active' in pg_state_list:
                    down = False
                    for value in pg_error_ls:
                        if value in pg_state_list:
                            down = True
                            break

                    if not down:
                        active_pg_counter += 1
                        if 'acting' in pg:
                            acting_osds = pg['acting']
                            active_osds_ls.extend(acting_osds)

        # Converting List to Set :
        active_osds_ls = list(set(active_osds_ls))
        # Check if 2147483647 exists in the list :
        if self.OSD_ID_IGNORE in active_osds_ls:
            active_osds_ls.remove(self.OSD_ID_IGNORE)
        self.active_pgs = active_pg_counter
        self.active_osds = len(active_osds_ls)
