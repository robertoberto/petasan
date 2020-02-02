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


import sys
import os
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.log import logger
from PetaSAN.core.common.cmd import call_cmd
from PetaSAN.core.ceph.api import CephAPI
from time import sleep
from flask import json

MARKER_FILE='/opt/petasan/config/mgr_installed_flag'

def create_mgr():

    logger.info('create_mgr() started')

    if not configuration().get_node_info().is_management:
        return True

    if os.path.exists(MARKER_FILE):
        logger.info('Ceph Manager already installed')
        return True

    cluster_name = configuration().get_cluster_name()
    current_node_name = configuration().get_node_info().name
    path = '/var/lib/ceph/mgr/{}-{}'.format(cluster_name,current_node_name)

    cmd = 'mkdir -p ' + path
    logger.info('create_mgr() cmd: ' + cmd)
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
        return False

    cmd = 'ceph --cluster {} auth get-or-create mgr.{}  mon '.format(cluster_name,current_node_name)
    cmd += ' \'allow profile mgr\' osd \'allow *\' mds \'allow *\'  '
    cmd += ' -o ' + path + '/keyring'
    logger.info('create_mgr() cmd: ' + cmd)
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
        return False

    cmd = 'ceph --cluster {} auth caps client.admin osd '.format(cluster_name)
    cmd += ' \'allow *\' mds \'allow *\' mon \'allow *\' mgr \'allow *\' '
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
        return False

    cmd = 'touch ' + path + '/systemd'
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
        return False

    cmd = 'touch ' + path + '/done'
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
        return False


    cmd = 'chown -R ceph:ceph /var/lib/ceph/mgr'
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
        return False

    cmd = 'mkdir -p /etc/systemd/system/ceph-mgr@.service.d'
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
        return False

    # stop copying the files because they aren't exist
    # cmd = 'cp /etc/systemd/system/ceph-mon@.service.d/override.conf /etc/systemd/system/ceph-mgr@.service.d'
    # if not call_cmd(cmd):
    #     logger.error('Error executing ' + cmd)
    #     return False

    cmd = 'systemctl enable ceph-mgr.target'
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
        return False

    cmd = 'systemctl enable ceph-mgr@{}.service'.format(current_node_name)
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
        return False

    cmd = 'systemctl start ceph-mgr@{}.service'.format(current_node_name)
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
        return False

    call_cmd('touch ' + MARKER_FILE)
    return True


if len(sys.argv) == 1 :
    # case of fresh install
    logger.info('create_mgr() fresh install')
    ret = create_mgr()
    if ret:
        logger.info('create_mgr() ended successfully')
        sys.exit(0)
    else:
        logger.error('create_mgr() error building manager')
        sys.exit(1)


if len(sys.argv) == 2 :
    # In case of upgrade, wait for cluster to be health_ok
    delay = int(sys.argv[1])
    while True:
        logger.info('create_mgr() upgrade install, waiting for cluster to be up')
        sleep(delay)
        ceph = CephAPI()
        health = ceph.get_health()
        if health is None:
            continue
        if health == 'HEALTH_OK' or health == 'HEALTH_WARN':
            logger.info('create_mgr() upgrade install, cluster is up')
            ret = create_mgr()
            if ret:
                logger.info('create_mgr() ended successfully')
                sys.exit(0)
            else:
                logger.error('create_mgr() error building manager')
                sys.exit(1)

sys.exit(1)

