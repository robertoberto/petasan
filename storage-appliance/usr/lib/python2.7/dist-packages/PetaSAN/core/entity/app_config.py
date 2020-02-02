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
from PetaSAN.core.entity.subnet_info import SubnetInfo


class AppConfig(object):
    def __init__(self):

        self.iqn_base = 'iqn.2016-05.com.petasan'
        self.iscsi1_subnet_mask = '255.255.255.0'
        self.iscsi1_vlan_id = ''
        self.iscsi1_auto_ip_from = '10.0.2.100'
        self.iscsi1_auto_ip_to = '10.0.2.254'
        self.iscsi2_subnet_mask = '255.255.255.0'
        self.iscsi2_vlan_id = ''
        self.iscsi2_auto_ip_from = '10.0.3.100'
        self.iscsi2_auto_ip_to =   '10.0.3.254'
        self.email_notify_smtp_server = ""
        self.email_notify_smtp_port = ""
        self.email_notify_smtp_email = ""
        self.email_notify_smtp_password = ""
        self.email_notify_smtp_security = 1
        self.wwn_fsid_tag = True


    def read_json(self, j):
        for key, value in json.loads(j).iteritems():
            self.__dict__[key]=value

    def write_json(self):
        j = json.dumps(self.__dict__)
        return j





