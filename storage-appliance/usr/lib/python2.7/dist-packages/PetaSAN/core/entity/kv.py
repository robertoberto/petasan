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


from json import JSONEncoder

from flask import json


class KV(object):
    def __init__(self):

        self.LockIndex = ""
        self.ModifyIndex = ""
        self.Value = ""
        self.Flags = ""
        self.Key = ""
        self.Session = ""
        self.CreateIndex = ""


    def load_json(self,j):
            self.__dict__ = json.loads(j)

class ConsulSession(object):
    def __init__(self):
        self.Node=""
        self.ID=""
        self.Name=""

    def load_json(self,j):
        self.__dict__ = json.loads(j)