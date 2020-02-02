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

import rados
from time import sleep
from PetaSAN.core.ceph.ceph_authenticator import CephAuthenticator
from PetaSAN.core.ceph.replication.users import Users
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI


class CephConnector:

    def __init__(self):
        pass

    def connect(self):

        RETRY_COUNTER = 7
        INTERVAL = 2
        i = 1

        while i <= RETRY_COUNTER:
            cluster = self.do_connect()
            if cluster != -1:
                break

            logger.warning("connect() retry({}) Cannot connect to ceph cluster.".format(str(i)))
            sleep(INTERVAL)  # wait 15 sec
            i += 1
            INTERVAL *= 2

        return cluster

    def do_connect(self):
        try:
            conf_api = ConfigAPI()

            # Get which ceph user is using this function #
            # ========================================== #
            users = Users()
            user_name = users.get_current_system_user().strip()
            if user_name == "root":
                user_name = "admin"

            # Get ceph user's keyring file path #
            # ================================= #
            ceph_auth = CephAuthenticator()

            cluster_name = configuration().get_cluster_name()

            cluster = rados.Rados(conffile=conf_api.get_ceph_conf_path(cluster_name),
                                  conf=dict(keyring=ceph_auth.get_keyring_path()), rados_id=user_name)
            cluster.connect()

            return cluster

        except Exception as e:
            logger.error("do_connect() Cannot connect to ceph cluster.")
            logger.exception(e.message)

            try:
                cluster.shutdown()
            except Exception as e:
                pass

            return -1
