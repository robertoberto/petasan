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

class ManageEcProfiles:

    def __init__(self):
        pass


    def get_ec_profiles(self):
        ceph_api = CephAPI()
        ec_profiles = ceph_api.get_ec_profiles()
        if 'default' in ec_profiles.keys():
            del ec_profiles['default']
        return ec_profiles


    def delete_ec_profile(self , profile_name):
        ceph_api = CephAPI()
        ceph_api.delete_ec_profile(profile_name)


    def add_ec_profile(self , profile_info):
        ceph_api = CephAPI()
        ceph_api.add_ec_profile(profile_info)