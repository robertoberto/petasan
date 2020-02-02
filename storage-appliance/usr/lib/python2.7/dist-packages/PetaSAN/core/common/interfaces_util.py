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

import subprocess
from PetaSAN.core.entity.network import DetectInterfaces
from PetaSAN.core.common.cmd import exec_command

DETECT_INTERFACES_SCRIPT='/opt/petasan/scripts/detect-interfaces.sh'


def get_interface_list():
    interface_list=[]
    p = subprocess.Popen(DETECT_INTERFACES_SCRIPT,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           stdin=subprocess.PIPE)
    stdout,stderr = p.communicate()

    lines = stdout.splitlines()
    for line in lines:
        interface=DetectInterfaces()
        kvs = line.split(',')
        for kv in kvs :
            if len( kv.split('=')) != 2 :
                continue
            k = kv.split('=')[0].strip()
            v =  kv.split('=')[1].strip()

            if k == 'device' :
                interface.name = v


            elif k == 'mac' :
                interface.mac = v

            elif k == 'pci' :
                interface.pci = v

            elif k == 'model' :
                interface.model = v

        if interface.name.startswith('eth') :
            interface_list.append(interface)

    return interface_list

