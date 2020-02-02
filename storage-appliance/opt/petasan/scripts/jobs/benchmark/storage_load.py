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
from PetaSAN.core.cluster.job_manager import JobManager
from PetaSAN.core.common.log import logger
from PetaSAN.core.entity.job import JobType

class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        parser.set_defaults(func=storage)
        parser.add_argument(
            '-d',help='Duration of interval for one sample..', required=True,type=int)


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


def storage(args):
    job_manager = JobManager()
    params = '-d {} '.format(args.d)
    for j in job_manager.get_running_job_list():
        if j.type == JobType.STORAGELOAD :
            logger.info("Cannot start storage load job for 'sar',")
            print("-1")
            return

    print( job_manager.add_job(JobType.STORAGELOAD,params))
    logger.info("Start storage load job for 'sar'")
    sys.exit(0)




if __name__ == '__main__':
  main(sys.argv[1:])


