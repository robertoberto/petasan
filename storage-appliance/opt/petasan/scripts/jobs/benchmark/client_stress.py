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
import sys
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.cluster.job_manager import JobManager
from PetaSAN.core.common.log import logger
from PetaSAN.core.entity.job import JobType
import signal
#123:deleteosd:-id@0@-disk_name@sdc:1482741855.job
class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        parser.set_defaults(func=client)

        parser.add_argument(
            '-d',help='Duration of benchmark test.', required=True,type=int)
        parser.add_argument(
            '-t',help='Number of threads.', required=True,type=int)
        parser.add_argument(
            '-b',help='Block size.',type=int,default=4000)
        parser.add_argument(
            '-m',help='Mode of test w:write or r:read. Note : read mode must run after write mode.', required=True)
        parser.add_argument(
            '-p',help='pool name.', required=True)


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


def client(args):

    job_manager = JobManager()
    params = '-d {} -t {} -b {} -m {} -p {}'.format(args.d,args.t,args.b,args.m,args.p)
    for j in job_manager.get_running_job_list():
        if j.type == JobType.CLIENTSTRESS :
            logger.info("Cannot start client stress job for 'rados',")
            print("-1")
            return

    print( job_manager.add_job(JobType.CLIENTSTRESS,params))
    logger.info("Start client stress job for rados")
    sys.exit(0)




if __name__ == '__main__':
  main(sys.argv[1:])

# sys.t=32
# sys.d = 10
# sys.b = 300
# sys.m='w'
#
# client(sys)

