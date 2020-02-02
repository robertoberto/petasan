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



from PetaSAN.core.security.api import UserAPI
from PetaSAN.core.entity.user_info import User

def get_list():
    user_api = UserAPI()
    for u in user_api.get_users():
        print u.user_name


def add_user(user):
    """

    :type user: User
    """
    if not user:
        user = User()
        user.user_name="mostafa"
    user_api = UserAPI()
    return user_api.add_user(user)

def del_user(name):
    user_api = UserAPI()
    return user_api.delete_user(name)

def get_user(name):
    user_api = UserAPI()
    u=user_api.get_user("mostafa")
    print  u.user_name,u.password,u.role_id

def update_user():
    """

    :type user: User
    """

    user = User()
    user.user_name="mostafa"
    user.password="1234"
    user.role_id=2
    user_api = UserAPI()
    return user_api.update_user(user)
print update_user()
#del_user("mostafa")
get_user("mostafa")
get_list()




