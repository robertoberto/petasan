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

from time import sleep
from PetaSAN.core.common.cmd import call_cmd
import argparse
import sys
from PetaSAN.core.common.log import logger
class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=False)
        parser.set_defaults(func=arping)

        parser.add_argument(
            '-c',help='Count of arping.',type=int,default=5)
        parser.add_argument(
            '-t',help='Number of tries.',type=int,default=5)
        parser.add_argument(
            '-i',help='Interval.',type=int,default=5)
        parser.add_argument(
            '-ip',help='IP address.',required=True,type=str)
        parser.add_argument(
            '-eth',help='eth name  eth0',required=True,type=str)


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


def arping(args):
    i =0
    cmd = "arping -A {} -I {} -c {}".format(args.ip,args.eth,args.c)
    logger.debug(cmd)

    while i < args.t:
        i+=1
        call_cmd(cmd)
        sleep(args.i)







if __name__ == '__main__':
   main(sys.argv[1:])

