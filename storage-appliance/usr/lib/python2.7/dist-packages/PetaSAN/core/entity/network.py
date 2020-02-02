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


class NetworkInterfaces(object):

    def __init__(self):
        self.name=""
        self.mac=""
        self.device_name=""
        self.is_management=False



class Bond(object):

    def __init__(self):
        self.name=""
        self.primary_interface= ""
        self.interfaces= []
        self.mode = ""
        self.is_jumbo_frames =False
    def load_json(self,j):
        self.__dict__ = json.loads(j)


class DetectInterfaces():
    def __init__(self):
        self.mac = ""
        self.pci = ""
        self.model = ""
        self.name = ""

    def get_dict(self):
        return  self.__dict__


    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))
        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()