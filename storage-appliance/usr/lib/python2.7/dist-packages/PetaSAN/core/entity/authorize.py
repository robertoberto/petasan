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


from json import JSONEncoder


class Page(object):
    def __init__(self):

        self.name = ""
        self.description = ""
        self.base_url = ""
        self.id=""
        self.parent_group =""

    def load_json(self,j):
            self.__dict__ = json.loads(j)

    def obj_dict(obj):
        return obj.__dict__


class Role(object):
    def __init__(self):

        self.name = ""
        self.description = ""
        self.id=""

    def load_json(self,j):
            self.__dict__ = json.loads(j)

class RolePages(object):
    def __init__(self):

        self.role_id = 0
        self.page_id = 0


    def load_json(self,j):
            self.__dict__ = json.loads(j)

