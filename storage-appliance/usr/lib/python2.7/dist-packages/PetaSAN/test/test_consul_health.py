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

import datetime
from PetaSAN.core.consul.api import ConsulAPI
import time
from PetaSAN.core.common.log import logger



con_api = ConsulAPI()
index = 0

while True:
    try:
        index = index + 1
        con_api.write_value('Test/' + str(index), None)
        print str(datetime.datetime.now())+' <<<<< Pass to add key Test/' + str(index)
    except Exception as exc:
        print str(datetime.datetime.now())+' >>>>> >>>>>> Error to add key Test/' + str(index)
        logger.exception(exc.message)
    time.sleep(3)
