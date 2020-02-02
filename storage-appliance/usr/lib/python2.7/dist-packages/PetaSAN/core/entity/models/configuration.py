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

class manage_network_form(object):

    def __init__(self):

        self.Subnet1 = ""
        self.Subnet1_Vlan_Id  = ''
        self.Subnet1_Ip_From = ""
        self.Subnet1_Ip_To = ""
        self.Subnet2 = ""
        self.Subnet2_Vlan_Id  = ''
        self.Subnet2_Ip_From = ""
        self.Subnet2_Ip_To = ""
        self.Subnet1_Info=""
        self.Subnet2_Info = ""
        self.Iqn = ""

    def load_json(self,j):
            self.__dict__ = json.loads(j)

