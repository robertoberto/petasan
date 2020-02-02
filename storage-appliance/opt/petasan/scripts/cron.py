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


import argparse
import os
import sys
import json
import datetime
from PetaSAN.core.cluster.configuration import configuration

from PetaSAN.core.common.log import logger

class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        subparser = parser.add_subparsers()

        subp_build = subparser.add_parser('build')
        subp_build.set_defaults(func = build)

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

def build(args):
    from PetaSAN.core.cluster.cron_manager import CronManager
    try:
        config = configuration()
        node_name = config.get_node_name()
        cron_manager = CronManager(node_name)
        cron_manager.build_crontab()
        sys.exit(0)

    except Exception as e:
        print("Error : build crontab , {}".format(str(e.message)))
        logger.error("Error : build crontab , {}".format(str(e.message)))
        sys.exit(-1)

# ######################################################################################################################



if __name__ == '__main__':
   main(sys.argv[1:])
