#! /usr/bin/python
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


import json
from PetaSAN.core.cluster.ntp import NTPConf

ntp = NTPConf()
server = ntp.get_ntp_server_local()
remote_ret = {}
remote_ret['success'] = True
remote_ret['ntp_server'] = server
print json.dumps(remote_ret)



