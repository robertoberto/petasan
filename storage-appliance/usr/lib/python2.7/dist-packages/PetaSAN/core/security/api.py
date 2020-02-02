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

import os
from PetaSAN.core.common.enums import ManageUserStatus
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.consul.base import BaseAPI
from PetaSAN.core.entity.authorize import Role, Page, RolePages
from PetaSAN.core.entity.user_info import User
import json




# default

class RoleAPI:
    path= os.path.dirname(ConfigAPI().get_cluster_info_file_path())
    def __init__(self):
        pass

    def get_roles(self):
        with open(self.path+'/roles.json', 'r') as f:
            data = json.load(f)
        roles = []
        for i in data:
            r = Role()
            r.load_json(json.dumps(i))
            roles.append(r)
        return roles

    def get_role_pages(self, role_id):
        with open(self.path+'/rolepages.json', 'r') as f:
            data = json.load(f)
        rp = []
        for i in data:
            p = RolePages()
            p.load_json(json.dumps(i))
            if int(role_id) == p.role_id:
                rp.append(p)
        return rp

    def is_page_allowed(self, page_id, role_id):
        with open(self.path+'/rolepages.json', 'r') as f:
            data = json.load(f)
        rp = []
        for i in data:
            p = RolePages()
            p.load_json(json.dumps(i))
            if int(role_id) == p.role_id and p.page_id == int(page_id):
                return True;
        return False

    def is_url_allowed(self, page_url, role_id):
        page = PageAPI()
        pg = page.get_page_by_url(page_url)
        if not pg:
            return False
        with open(self.path+'/rolepages.json', 'r') as f:
            data = json.load(f)
        for i in data:
            r = RolePages()
            r.load_json(json.dumps(i))
            if int(role_id) == int(r.role_id) and int(pg.id) == int(r.page_id):
                return True;
        return False

    def is_page_allowed_by_name(self, page_name, role_id):
        page = PageAPI()
        pg = page.get_page(page_name)
        if not pg:
            return False
        with open(self.path+'/rolepages.json', 'r') as f:
            data = json.load(f)
        for i in data:
            r = RolePages()
            r.load_json(json.dumps(i))
            if int(role_id) == int(r.role_id) and int(pg.id) == int(r.page_id):
                return True;
        return False


    def is_allowed_by_parent_name(self, parent_name, role_id):
        is_parent_allowed = False
        pages = []
        pageAPI = PageAPI()
        rp = RolePages()
        roleAPI = RoleAPI()
        pages = pageAPI.get_pages()
        rps = roleAPI.get_role_pages(role_id)
        for page in pages:
            for role in rps:
             if page.id == role.page_id:
                if page.parent_group == parent_name:
                    return True

        return False

    ''''
    with open('roles.json', 'w') as f:
    json.dump(get_roles(),f)

    with open('pages.json', 'w') as f:
    json.dump(get_pages(),f)

    with open('rolepages.json', 'w') as f:
    json.dump(rolepages(),f)

    with open('roles.json', 'r') as f:
     data = json.load(f)
     for  i in data:
         r = Role()
         r.load_json(json.dumps(i))
         print r.id,r.name

    '''''


class PageAPI:
    path= os.path.dirname(ConfigAPI().get_cluster_info_file_path())
    def __init__(self):
        pass

    def get_pages(self):
        with open(self.path+'/pages.json', 'r') as f:
            data = json.load(f)
        pages = []
        for i in data:
            p = Page()
            p.load_json(json.dumps(i))
            pages.append(p)
        return pages

    def get_page(self, Page_name):
        with open(self.path+'/pages.json', 'r') as f:
            data = json.load(f)
        for i in data:
            p = Page()
            p.load_json(json.dumps(i))
            if p.name == Page_name:
                return p

        return None

    def get_page_by_url(self, Page_url):
        with open(self.path+'/pages.json', 'r') as f:
            data = json.load(f)
        for i in data:
            p = Page()
            p.load_json(json.dumps(i))
            if p.base_url == Page_url:
                return p

        return None


class UserAPI:
    user_path = ConfigAPI().get_user_path()

    def __init__(self):
        con = BaseAPI()

        pass

    def get_users(self):
        cons = BaseAPI()
        users = []
        if not cons.read_recurse(self.user_path):
            self.add_user(self.__admin__())

        session_data = cons.read_recurse(self.user_path)
        if session_data:
            for s in session_data:
                u = User()
                u.load_json(s['Value'])
                users.append(u)

        return users

    def get_user(self, user_name):
        cons = BaseAPI()
        users = []
        user_name = str(user_name).lower()
        if not cons.read_recurse(self.user_path):
            self.add_user(self.__admin__())

        user_data = cons.read_value(self.user_path + user_name)
        if user_data:
            u = User()
            u.load_json(user_data)
            return u

        return None

    def add_user(self, user):
        """

        :type user: User
        """
        try:
            user.user_name = str(user.user_name).lower()
            cons = BaseAPI()
            if not cons.read_value(self.user_path + user.user_name):
                cons.write_value(self.user_path + user.user_name, user.get_json())
                return ManageUserStatus().done
            else:
                return ManageUserStatus().exists
        except Exception as ex:
            return ManageUserStatus().error

    def delete_user(self, user_name):
        try:
            if str(user_name).lower() == "admin":
                return ManageUserStatus().error
            cons = BaseAPI()
            cons.delete_key(self.user_path + user_name)
            return ManageUserStatus().done
        except Exception as ex:
            return ManageUserStatus().error

    def update_user(self, user):
        """

        :type user: User
        """
        try:
            cons = BaseAPI()
            user.user_name = str(user.user_name).lower()
            if cons.read_value(self.user_path + user.user_name):
                cons.write_value(self.user_path + user.user_name, user.get_json())
                return ManageUserStatus().done
            else:
                return ManageUserStatus().not_exists
        except Exception as ex:
            return ManageUserStatus().error

    def __admin__(self):
        user = User()
        user.user_name = "admin"
        user.password = "password"
        user.role_id = 1
        return user
