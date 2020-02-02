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

from PetaSAN.core.common.enums import ManageUserStatus
from PetaSAN.core.security.api import RoleAPI, UserAPI
from PetaSAN.core.entity.user_info import User




class ManageUser:
    def __init__(self):
        pass

    def get_roles(self):
        role_api = RoleAPI()
        return role_api.get_roles()

    def get_users(self):
        user_api = UserAPI()
        return user_api.get_users()

    def add_user(self, user):
        """

        :type user: User
        """
        user_api = UserAPI()
        return user_api.add_user(user)

    def delete_user(self, user_name):
        user_api = UserAPI()
        return user_api.delete_user(user_name)

    def update_user(self, user):
        """

        :type user: User
        """
        user_api = UserAPI()
        return user_api.update_user(user)


    def update_password(self, user_name,password):

        user_api = UserAPI()
        user = user_api.get_user(user_name)
        if user:
            user.password = password
            return user_api.update_user(user)
        else:
            return ManageUserStatus().error

    def get_user(self, user_name):
          user_api = UserAPI()
          return user_api.get_user(user_name)

