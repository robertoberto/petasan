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

from ConfigParser import RawConfigParser
import base64
from flask import json
import os
import struct
import time
import uuid
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.cluster import NodeInfo




class CephConf(RawConfigParser):
    def optionxform(self, s):
        s = s.replace('_', ' ')
        s = '_'.join(s.split())
        return s

    def safe_get(self, section, key):
        """
        Attempt to get a configuration value from a certain section
        in a ``cfg`` object but returning None if not found. Avoids the need
        to be doing try/except {ConfigParser Exceptions} every time.
        """
        try:
            #Use full parent function so we can replace it in the class
            # if desired
            return ConfigParser.RawConfigParser.get(self, section, key)
        except (ConfigParser.NoSectionError,
                ConfigParser.NoOptionError):
            return None

def get_net_size(netmask):
    netmask = netmask.split('.')
    binary_str = ''
    for octet in netmask:
        binary_str += bin(int(octet))[2:].zfill(8)
    return str(len(binary_str.rstrip('0')))

def generate_auth_key():
    key = os.urandom(16)
    header = struct.pack(
        '<hiih',
        1,                 # le16 type: CEPH_CRYPTO_AES
        int(time.time()),  # le32 created: seconds
        0,                 # le32 created: nanoseconds,
        len(key),          # le16: len(key)
    )
    return base64.b64encode(header + key)




def new():
    conf = configuration()
    current_node_name = conf.get_node_info().name
    clu = conf.get_cluster_info()

    logger.info('Creating new cluster named %s', clu.name)
    cfg = CephConf()
    cfg.add_section('global')

    fsid = uuid.uuid4()
    cfg.set('global', 'fsid', str(fsid))


    # if networks were passed in, lets set them in the
    # global section

    cfg.set('global', 'public network', str(clu.backend_1_base_ip)+"/"+get_net_size(str(clu.backend_1_mask)))

    cfg.set('global', 'cluster network', str(clu.backend_2_base_ip)+"/"+get_net_size(str(clu.backend_2_mask)))

    mon_initial_members = []
    mon_host = []



    config_api = ConfigAPI()
    for i in clu.management_nodes:
        node_info=NodeInfo()
        node_info.load_json(json.dumps(i))
        mon_initial_members.append(node_info.name)
        mon_host.append(node_info.backend_1_ip)






    cfg.set('global', 'mon initial members', ', '.join(mon_initial_members))
    # no spaces here, see http://tracker.newdream.net/issues/3145
    cfg.set('global', 'mon host', ','.join(mon_host))

    # override undesirable defaults, needed until bobtail

    # http://tracker.ceph.com/issues/6788
    cfg.set('global', 'auth cluster required', 'cephx')
    cfg.set('global', 'auth service required', 'cephx')
    cfg.set('global', 'auth client required', 'cephx')

    cfg.set('global', 'mon clock drift allowed', '.300')
    cfg.set('global', 'osd pool default size', '2')
    cfg.set('global', 'max open files', '131072')

    # http://tracker.newdream.net/issues/3138
    cfg.set('global', 'filestore xattr use omap', 'true')

    path = '{name}.conf'.format(
        name=clu.name,
        )

    new_mon_keyring(clu.name)

    logger.info('Writing initial config to %s...', path)
    tmp = '%s.tmp' % path
    with file(tmp, 'w') as f:
        cfg.write(f)
    try:
        os.rename(tmp, path)
    except OSError as e:
           raise




def new_mon_keyring(cluster):
    logger.debug('Creating a random mon key...')
    mon_keyring = '[mon.]\nkey = %s\ncaps mon = allow *\n' % generate_auth_key()

    keypath = '{name}.mon.keyring'.format(
        name=cluster,
        )
    oldmask = os.umask(077)
    logger.debug('Writing monitor keyring to %s...', keypath)
    try:
        tmp = '%s.tmp' % keypath
        with open(tmp, 'w', 0600) as f:
            f.write(mon_keyring)
        try:
            os.rename(tmp, keypath)
        except OSError as e:
                raise
    finally:
        os.umask(oldmask)
















