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


import argparse
import subprocess
import sys
from time import sleep

from PetaSAN.core.cluster.network import Network
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.log import logger
from PetaSAN.core.consul.api import ConsulAPI
from PetaSAN.core.lio.network import NetworkAPI
from PetaSAN.core.entity.disk_info import DiskMeta
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.config.api import ConfigAPI


class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        parser.set_defaults(func=move)

        parser.add_argument(
            '-id', help='Disk id such as 00006.', required=True, type=str)
        parser.add_argument(
            '-ip', help='IP address of path.', required=True, type=str)

        args = parser.parse_args()

        return args


__app_conf = ConfigAPI()
__node_info = configuration().get_node_info()
__ceph_api = CephAPI()
__disk_id = ''
__ip = ''
__network = NetworkAPI()
__consul_api = ConsulAPI()
__session = None


def main_catch(func, args):
    try:
        func(args)

    except Exception as e:
        logger.error(e.message)
        print ('Exception occurred.')
        # print (e.message)


def main(argv):
    args = Prepare().parser()
    main_catch(args.func, args)


def delete_ip(ip, eth, subnet):
    p = subprocess.Popen(["ip", "address", "del", "/".join([ip, subnet]), "dev", eth], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out = p.stderr.read()
    print out


def is_ip_configured(_ip):
    ips = Network().get_all_configured_ips()
    for ip, eth_name in ips.iteritems():
        ip, mask = str(ip).split("/")
        if ip == _ip:
            return True
    return False




def get_pool_by_disk(disk_id):

    consul_api = ConsulAPI()
    ceph_api = CephAPI()
    pool = consul_api.get_disk_pool(disk_id)
    if pool:
        return pool
    pool = ceph_api.get_pool_bydisk(disk_id)
    if pool:
        return pool

    return None


def move(args):

    __ip = args.ip
    __disk_id = args.id
    index = -1

    pool = get_pool_by_disk(__disk_id)
    if not pool: 
        print 'disk id does not exist'
        sys.exit(0)

    image_name = __app_conf.get_image_name_prefix() + __disk_id
    all_image_meta = __ceph_api.read_image_metadata(image_name,pool)
    petasan_meta = all_image_meta.get(__app_conf.get_image_meta_key())
    disk_meta = DiskMeta()
    disk_meta.load_json(petasan_meta)
    path_obj = disk_meta.get_paths()

    for key, val in __consul_api.get_sessions_dict(__app_conf.get_iscsi_service_session_name(),
                                                   __node_info.name).iteritems():
        __session = key

    out = "Path does not exist."
    for i in path_obj:
        index += 1
        if i.ip == __ip:

            delete_ip(i.ip, i.eth, i.subnet_mask)
            sleep(3)
            if is_ip_configured(i.ip):
                out = "Could not delete ip."
                break

            if __consul_api.is_path_locked_by_session(
                                            __app_conf.get_consul_disks_path() + __disk_id + "/" + str(index + 1),
                                            __session):
                __consul_api.release_disk_path(__app_conf.get_consul_disks_path() + __disk_id + "/" + str(index + 1),
                                               __session, None)
                out = "Done"
            else:
                out = "Path is not acquired by this node."
            break

    print out
    sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])



