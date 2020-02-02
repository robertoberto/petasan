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

import os
import sys
from time import sleep, time
from PetaSAN.core.ceph.ceph_disk_lib import *
from PetaSAN.core.common.cmd import *
from PetaSAN.core.common.log import logger
from PetaSAN.core.cluster.configuration import configuration
import shutil
import subprocess

# ===============================================
logger.info("Stopping ceph services")
if not call_cmd("systemctl stop ceph\*.service ceph\*.target"):
    logger.error("Error executing: systemctl stop ceph\*.service ceph\*.target")


# ===============================================
logger.info("Start cleaning config files")

subprocess.call('rm -rf /etc/ceph', shell=True)
subprocess.call('rm -rf /opt/petasan/config/etc/ceph', shell=True)
subprocess.call('mkdir -p /opt/petasan/config/etc/ceph', shell=True)
subprocess.call('ln -s /opt/petasan/config/etc/ceph /etc/ceph', shell=True)

subprocess.call('rm -rf /var/log/ceph/', shell=True)
subprocess.call('mkdir -p  /var/log/ceph', shell=True)
subprocess.call('chown -R ceph:ceph  /var/log/ceph', shell=True)

subprocess.call('rm -rf /var/run/ceph/', shell=True)
subprocess.call('mkdir -p  /var/run/ceph', shell=True)
subprocess.call('chown -R ceph:ceph  /var/run/ceph', shell=True)

subprocess.call('rm -rf /var/lib/ceph', shell=True)
subprocess.call('mkdir -p  /var/lib/ceph', shell=True)
subprocess.call('mkdir -p  /var/lib/ceph/osd', shell=True)
subprocess.call('mkdir -p  /var/lib/ceph/mgr', shell=True)
subprocess.call('chown -R ceph:ceph  /var/lib/ceph', shell=True)

subprocess.call('rm -rf /tmp', shell=True)
subprocess.call('mkdir -p /tmp', shell=True)
subprocess.call('chmod 1777 /tmp', shell=True)

subprocess.call('rm -rf /etc/hosts', shell=True)
subprocess.call('rm -rf /opt/petasan/config/etc/hosts', shell=True)
subprocess.call('touch /opt/petasan/config/etc/hosts', shell=True)
subprocess.call('ln -s /opt/petasan/config/etc/hosts /etc/hosts', shell=True)

subprocess.call('rm -rf /etc/systemd/system/ceph-mon@.service.d/', shell=True)
subprocess.call('rm -rf /etc/systemd/system/ceph-osd@.service.d/', shell=True)
subprocess.call('rm -rf /etc/systemd/system/ceph-mgr@.service.d/', shell=True)
os.makedirs("/etc/systemd/system/ceph-mon@.service.d/")
os.makedirs("/etc/systemd/system/ceph-osd@.service.d/")
os.makedirs("/etc/systemd/system/ceph-mgr@.service.d/")


content ="[Service]\n\
Environment=CLUSTER={}"
# stop creating override.conf files
# with open("/etc/systemd/system/ceph-mon@.service.d/override.conf", 'w', ) as f:
#     f.write(content.format(configuration().get_cluster_name()))
# with open("/etc/systemd/system/ceph-osd@.service.d/override.conf", 'w', ) as f:
#     f.write(content.format(configuration().get_cluster_name()))
# with open("/etc/systemd/system/ceph-mgr@.service.d/override.conf", 'w', ) as f:
#     f.write(content.format(configuration().get_cluster_name()))
#
#
# logger.info('End cleaning config files')

# ===============================================
logger.info("Starting ceph services")
if not call_cmd("systemctl start ceph.target"):
    logger.error("Can not start ceph services.")

sys.exit(0)

