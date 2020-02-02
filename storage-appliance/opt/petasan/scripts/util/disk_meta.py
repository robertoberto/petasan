#! /usr/bin/python
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

from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.ceph.ceph_authenticator import CephAuthenticator
from PetaSAN.core.ceph.replication.users import Users

import argparse
import sys
import rados
from PetaSAN.core.ceph.mt_meta_reader import meta_key
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI


class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        subparser = parser.add_subparsers()

        # Clear Disk Scripts : read_disks_metadata , set_disk_metadata
        # ============================================================
        subp_read_metadata = subparser.add_parser('read')
        subp_read_metadata.set_defaults(func = read_disks_metadata)
        subp_read_metadata.add_argument('--image', help='image name', required=True)
        subp_read_metadata.add_argument('--pool', help='pool name', required=True)

        subp_write_metadata = subparser.add_parser('write')
        subp_write_metadata.set_defaults(func = set_disk_metadata)
        subp_write_metadata.add_argument('--image', help='image name', required=True)
        subp_write_metadata.add_argument('--pool', help='pool name', required=True)
        subp_write_metadata.add_argument('--file', help='file path', required=False)

        args = parser.parse_args()
        return args


def main_catch(func, args):
    try:
        func(args)

    except Exception as e:
        print ('Exception message :')
        print (e.message)


def main(argv):
    args = Prepare().parser()
    main_catch(args.func, args)

# ######################################################################################################################

def read_disks_metadata(args):
    io_ctx = None
    ceph_api = CephAPI()
    cluster = None

    try:
        cluster = ceph_api.connect()
        io_ctx = cluster.open_ioctx(args.pool)

        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        config = configuration()
        cluster_name = config.get_cluster_name()

        cmd = "rbd info " + args.pool + "/" + str(args.image) + " " + ceph_auth.get_authentication_string() + " --cluster " + cluster_name + " | grep rbd_data"

        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                cluster.shutdown()
                print("Cannot get image meta object from rbd header.")
                sys.exit(-1)

        rbd_data = stdout.rstrip().strip()
        dot_indx = rbd_data.rfind(".")

        image_id = rbd_data[(dot_indx+1):]

        rbd_header_object = "rbd_header." + image_id

        try:
            ret = io_ctx.get_xattr(rbd_header_object, meta_key)
        except:
            ret = io_ctx.get_xattr(rbd_header_object[:-1], meta_key)

        io_ctx.close()
        cluster.shutdown()

        if ret:
            print(ret)
            sys.stdout.flush()
            sys.exit(0)
        else:
            # Non-PetaSAN Disk :
            sys.exit(-1)

    except Exception as e:
        print("Error in executing script function : read_disks_metadata , " + str(e.message))
        io_ctx.close()
        cluster.shutdown()
        sys.exit(-1)



# ######################################################################################################################

def set_disk_metadata(args):
    io_ctx = None
    ceph_api = CephAPI()
    cluster = None

    try:
        cluster = ceph_api.connect()
        io_ctx = cluster.open_ioctx(args.pool)

        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        config = configuration()
        cluster_name = config.get_cluster_name()

        if args.file:
            with open(str(args.file), 'r') as file:
                disk_metadata_str = file.read()

        else:
            disk_metadata = sys.stdin.readlines()
            disk_metadata_str = ''.join(str(line) for line in disk_metadata)                 # converting list to string

        # read object meta :
        cmd = "rbd info " + args.pool + "/" + str(args.image) + " " + ceph_auth.get_authentication_string() + " --cluster " + cluster_name + " | grep rbd_data"
        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                cluster.shutdown()
                print("Cannot get image meta object from rbd header.")

        rbd_data = stdout.rstrip().strip()
        dot_indx = rbd_data.rfind(".")

        image_id = rbd_data[(dot_indx+1):]
        
        meta_object = "rbd_header." + image_id
        attr_object = meta_object

        io_ctx.set_xattr(str(attr_object), str(ConfigAPI().get_image_meta_key()), disk_metadata_str)
        io_ctx.close()
        cluster.shutdown()
        sys.exit(0)

    except Exception as e:
        print("Error in executing script function : set_disk_metadata , " + str(e.message))
        io_ctx.close()
        cluster.shutdown()
        sys.exit(-1)

# ######################################################################################################################


if __name__ == '__main__':
   main(sys.argv[1:])

