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


class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=False)
        parser.set_defaults(func=add_cache)
        parser.add_argument('-disk_name')
        parser.add_argument('-partitions')

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


def add_cache(args):
    if not configuration().get_node_info().is_storage:
        print("-1")
        return

    job_manager = JobManager()
    params = '-disk_name {} -partitions {}'.format(args.disk_name, args.partitions)

    # Getting all running jobs :
    for j in job_manager.get_running_job_list():
        if j.type == JobType.DELETEOSD or j.type == JobType.ADDDISK or \
                        j.type == JobType.ADDJOURNAL or j.type == JobType.DELETEJOURNAL or \
                        j.type == JobType.ADDCACHE or j.type == JobType.DELETECACHE:
            logger.info("Cannot start add cache job for disk {}. There ara running jobs.".format(args.disk_name))
            print("-1")
            return

    print(job_manager.add_job(JobType.ADDCACHE, params))
    logger.info("Start add cache job for disk {}.".format(args.disk_name))
    sys.exit()


if __name__ == '__main__':
    main(sys.argv[1:])


