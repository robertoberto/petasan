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
# 123:addosd:-disk_name@sdd:1482741855.job


class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=False)
        parser.set_defaults(func=add_osd)
        parser.add_argument('-disk_name', help='The selected disk name to be added as OSD.', required=True)
        parser.add_argument('-journal', help='Journal disk name.', default="")
        parser.add_argument('-cache', help='Cache disk name.', default="")
        parser.add_argument('-cache_type', help='Cache type.', default="")

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


def add_osd(args):
    if not configuration().get_node_info().is_storage:
        print("-1")
        return

    job_manager = JobManager()

    # If no journal and no cache :
    if str(args.journal) == "" and str(args.cache) == "":
        params = '-disk_name {}'.format(args.disk_name)

    # If journal but no cache :
    elif str(args.journal) != "" and str(args.cache) == "":
        params = '-disk_name {} -journal {}'.format(args.disk_name, args.journal)

    # If cache but no journal :
    elif str(args.journal) == "" and str(args.cache) != "" and str(args.cache_type) != "":
        params = '-disk_name {} -cache {} -cache_type {}'.format(args.disk_name, args.cache, args.cache_type)

    # If both journal and cache :
    else:
        params = '-disk_name {} -journal {} -cache {} -cache_type {}'.format(args.disk_name, args.journal,
                                                                             args.cache, args.cache_type)

    # Getting all running jobs :
    for j in job_manager.get_running_job_list():
        if j.type == JobType.DELETEOSD or j.type == JobType.ADDDISK or \
                        j.type == JobType.ADDJOURNAL or j.type == JobType.DELETEJOURNAL or \
                        j.type == JobType.ADDCACHE or j.type == JobType.DELETECACHE:
            logger.info("Cannot start add job to create osd for disk : {}. There ara running jobs.".
                        format(args.disk_name))
            print("-1")
            return

    print(job_manager.add_job(JobType.ADDDISK, params))
    logger.info("Start add osd job for disk {}.".format(args.disk_name))
    sys.exit()


if __name__ == '__main__':
    main(sys.argv[1:])

