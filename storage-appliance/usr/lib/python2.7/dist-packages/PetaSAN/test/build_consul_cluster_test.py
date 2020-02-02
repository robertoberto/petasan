#!/usr/bin/env python
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

from PetaSAN.core.consul.deploy.build import *
# import  PetaSAN.core.consul.deploy.build


# consul_conf = ConsulLeaderStarter()

status = build_consul()
print('build_consul_config')
if status is not None:
    print " >>>>>>>>>>>>>>>>>>>>>>>>>>>>> Build consul error list {} <<<<<<<<<<<<<<<<<<<<<<<<<<<<".format\
        (status.failed_tasks)
    print " >>>>>>>>>>>>>>>>>>>>>>>>>>>>> Build consul status is {} <<<<<<<<<<<<<<<<<<<<<<<<<<<<".format(status.success)
