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

import logging
from logging.handlers import RotatingFileHandler
import os

if not os.path.exists("/opt/petasan/log/"):
   os.makedirs("/opt/petasan/log/")


__info_path ='/opt/petasan/log/PetaSAN.log'
__debug_path= '/opt/petasan/log/PetaSAN.debug.log'


logger = logging.getLogger()
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)




handler_info = RotatingFileHandler(__info_path, mode='a', maxBytes=10*1024*1024, backupCount=1, encoding=None, delay=0)
handler_info.setLevel(logging.INFO)
# create a logging format for info
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',datefmt=' %d/%m/%Y %H:%M:%S')
handler_info.setFormatter(formatter)
# add the info handler to the logger
logger.addHandler(handler_info)





if logger.level == logging.DEBUG:
   handler_debug = RotatingFileHandler(__debug_path, mode='a', maxBytes=10*1024*1024, backupCount=1, encoding=None, delay=0)
   handler_debug.setLevel(logging.DEBUG)
   # create a debug logging format
   formatter_debug = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',datefmt=' %d/%m/%Y %H:%M:%S')
   handler_debug.setFormatter(formatter_debug)
   logger.addHandler(handler_debug)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("ceph_disk").setLevel(logging.WARNING)

