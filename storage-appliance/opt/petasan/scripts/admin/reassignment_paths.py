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
from PetaSAN.backend.mange_path_assignment import MangePathAssignment
from PetaSAN.core.common.log import logger
import argparse


class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        subparser = parser.add_subparsers()
        subnp_server = subparser.add_parser('server')
        subnp_server.set_defaults(func=server)


        subp_path_host = subparser.add_parser('path_host')
        subp_path_host.set_defaults(func=path_host)
        subp_path_host.add_argument(
            '-ip',
            help='Disk path ip.', required=True
        )
        subp_path_host.add_argument(
            '-disk_id',
            help='Disk ID.', required=True
        )
        args = parser.parse_args()
        return args


def main_catch(func, args):
    try:
        func(args)

    except Exception as e:
        logger.error(e.message)
        print ('-1')



def main(argv):
    args = Prepare().parser()
    main_catch(args.func, args)


def server(args):

    try:
        logger.info("Reassignment paths script invoked to run process action.")
        MangePathAssignment().process()
    except Exception as ex:
        logger.error("error process reassignments actions.")
        logger.exception(ex.message)
        print (-1)
        sys.exit(-1)



def path_host(args):
    logger.info("Reassignment paths script invoked to run clean action.")
    if MangePathAssignment().clean_source_node(args.ip,args.disk_id):
        print "0"
        return

    print "-1"






if __name__ == '__main__':
   main(sys.argv[1:])
