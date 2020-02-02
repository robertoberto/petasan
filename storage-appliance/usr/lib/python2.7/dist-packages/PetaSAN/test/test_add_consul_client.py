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

from PetaSAN.core.consul.deploy.build import create_consul_client_config, start_client



# x = ['A', 'S', 'M', 'A', 'A']
# print(repr(x))
# client_ip = '192.168.17.14'# raw_input('Enter the IP of the client that needs to join the consul cluster: ')
if create_consul_client_config():
    start_client()