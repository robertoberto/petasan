#!/usr/bin/python
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


# This script will detect all network interfaces and
# create the udev rule to assign stable names to network
# cards based on their MAC address ...

import sys
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.common.log import logger


device_mac_dict = {}

# Getting all ethernet network devices #
# ------------------------------------ #
cmd1 = "find /sys/class/net/* | grep -E \'\/(eth)\' | grep -v \'\.\'"

ret1, stdout1, stderr1 = exec_command_ex(cmd1)

if ret1 != 0:
    if stderr1:
        logger.error("Cannot detect network devices paths , {}".format(str(stderr1)))
        sys.exit(-1)

stdout = stdout1.rstrip()
devices_ls = stdout.splitlines()


# Getting MAC Address for each network device #
# ------------------------------------------- #
for device_path in devices_ls:
    # Getting device name :
    device_name = device_path.split("/")[4]

    # Getting device MAC Address :
    cmd2 = "ethtool -P {}".format(device_name)
    ret2, stdout2, stderr2 = exec_command_ex(cmd2)

    if ret2 != 0:
        if stderr2:
            logger.error("Cannot get MAC Address of device {} , {}".format(device_name, str(stderr2)))
            sys.exit(-1)

    mac_address = stdout2[19:]
    mac_address = mac_address.rstrip()

    device_mac_dict[device_name] = mac_address


# Generating "/etc/udev/rules.d/70-persistent-net.rules" file #
# ----------------------------------------------------------- #
try:
    with open("/etc/udev/rules.d/70-persistent-net.rules", 'wb+') as f:
        for device, mac in device_mac_dict.iteritems():
            f.write(
                '\nSUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{}=="{}", ATTR{}=="1", KERNEL=="eth*", NAME="{}" '.format(
                    "{address}", mac, "{type}", device))
        f.close()
    sys.exit(0)

except Exception as e:
    logger.error("Cannot generate /etc/udev/rules.d/70-persistent-net.rules file , {}".format(str(e.message)))
    sys.exit(-1)


