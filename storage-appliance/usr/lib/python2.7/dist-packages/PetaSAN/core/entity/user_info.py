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





class User(object):
    def __init__(self):

        self.name=""
        self.user_name = ""
        self.password = ""
        self.email = ""
        self.role_id = ""
        self.notfiy = False

    def load_json(self,j):
            self.__dict__ = json.loads(j)

    def get_json(self):
        i = json.dumps(self.__dict__)
        return i


