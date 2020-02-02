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

from os import listdir
import re
import subprocess
from PetaSAN.core.entity.ph_disk import DiskInfo

DETECT_DISKS_SCRIPT='/opt/petasan/scripts/detect-disks.sh'


def get_disk_list():
    disk_info_list=[]

    p = subprocess.Popen(DETECT_DISKS_SCRIPT,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           stdin=subprocess.PIPE)
    stdout,stderr = p.communicate()

    lines = stdout.splitlines()
    for line in lines:
        di=DiskInfo()
        kvs = line.split(',')
        for kv in kvs :
            if len( kv.split('=')) != 2 :
                continue
            k = kv.split('=')[0].strip()
            v =  kv.split('=')[1].strip()

            if k == 'device' :
                di.name = v

            elif k == 'size' :
                size = int(v) / 2 / 1024 / 1024
                if size < 1024 :
                    di.size = str(size) + " GB"
                else :
                    size = float(size) / 1024
                    size = round(size, 2)
                    di.size = str(size) + " TB"

            elif k == 'vendor' :
                di.vendor = v

            elif k == 'model' :
                di.model = v

            elif k == 'serial' :
                di.serial = v

            elif k == 'ssd' :
                if v == 'Yes':
                    di.is_ssd = True
                else:
                    di.is_ssd = False

            elif k == 'bus' :
                di.type = v

        if di.name.startswith('sd') or di.name.startswith('xvd') or di.name.startswith('nvme') :
            disk_info_list.append(di)

    return disk_info_list
