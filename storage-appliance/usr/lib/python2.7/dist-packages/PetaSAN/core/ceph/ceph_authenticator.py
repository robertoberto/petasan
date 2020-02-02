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

from PetaSAN.core.ceph.replication.users import Users
from PetaSAN.core.cluster.configuration import configuration


class CephAuthenticator:
    def __init__(self):
        pass


    def get_authentication_string(self):
        cluster_name = configuration().get_cluster_name()
        users = Users()
        user_name = users.get_current_system_user().strip()

        if user_name == "root":
            return ""

        auth_string = " -n client." + user_name + " --keyring=/etc/ceph/" + cluster_name +".client." + user_name + ".keyring"
        return auth_string


    def get_keyring_path(self):
        cluster_name = configuration().get_cluster_name()
        users = Users()
        user_name = users.get_current_system_user().strip()

        if user_name == "root":
            user_name = "admin"

        path = "/etc/ceph/" + cluster_name + ".client." + user_name + ".keyring"
        return path


# ######################################################################################################################
