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

class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        parser.set_defaults(func=get_job)
        parser.add_argument(
            '-id',help='Job id', required=True,type=int)

        parser.add_argument(
            '-t',help='1 job status, 2 get job output', required=True,type=int)


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


def get_job(args):
    job_manager = JobManager()
    # Get Status
    if args.t ==1:
        print( int(job_manager.is_done(args.id)))
    # Get output
    elif args.t ==2:
        print (job_manager.get_job_output(args.id))

    sys.exit(0)



if __name__ == '__main__':
  main(sys.argv[1:])

