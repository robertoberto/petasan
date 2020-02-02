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

from PetaSAN.core.consul.deploy.build import consul_server_conf
import json




def read_key():
    # get the security code from the server we're connecting to
    consul_server_conf_file = consul_server_conf + '/config.json'
    file = open(consul_server_conf_file)
    config_file = json.load(file)
    encrypt = config_file['encrypt']
    print(encrypt)
    # print('OK')
    return encrypt

read_key()