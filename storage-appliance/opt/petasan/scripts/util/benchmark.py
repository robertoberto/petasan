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


from PetaSAN.core.ceph.api import CephAPI

import argparse
import sys
from PetaSAN.backend.cluster.benchmark import Benchmark
from PetaSAN.core.common.log import logger


##########  how to use
# python /opt/petasan/scripts/benchmark.py storage -d 5


class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        subparser = parser.add_subparsers()
        subp_storage = subparser.add_parser('storage', help='Collect node state [cpu,ram,hd,network].')
        subp_storage.set_defaults(func=storage)
        subp_storage.add_argument(
            '-d',
            help='Duration of interval for one sample.', required=True,type=int
        )

        subp_client = subparser.add_parser('client',
                                           help='Run rados benchmark on this client.Note:'
                                                ' client must be connected to ceph and careate petasan_benchmark bool .')
        subp_client.set_defaults(func=client)
        subp_client.add_argument(
            '-d',help='Duration of benchmark test.', required=True,type=int)
        subp_client.add_argument(
            '-t',help='Number of threads.', required=True,type=int)
        subp_client.add_argument(
            '-b',help='Block size.',type=int,default=4096)
        subp_client.add_argument(
            '-m',help='Mode of test w:write or r:read. Note : read mode must run after write mode.', required=True)
        subp_client.add_argument(
            '-p',help='pool name.', required=True)


        subp_manager = subparser.add_parser('manager',help='Run rados benchmark on this manager.')
        subp_manager.set_defaults(func=manager)
        subp_manager.add_argument(
            '-d',help='Duration of benchmark test.', required=True,type=int)
        subp_manager.add_argument(
            '-t',help='Number of threads.', required=True,type=int)
        subp_manager.add_argument(
            '-type',help='Type of test[1=4M Throughput ,2=4K IOPS].',required=True)
        subp_manager.add_argument(
            '-c',help="Clients.Ex: 'ps-01,ps-02'", required=True)
        subp_manager.add_argument(
            '-p',help='pool name.', required=True)
        subp_manager.add_argument(
            '--cleanup',help='clean test objects.', required=True)


        subp_clean = subparser.add_parser('clean',help='Cleans up objects after benchmark.')
        subp_clean.set_defaults(func=clean)
        subp_clean.add_argument(
            '-p',help='pool name.', required=True)
 

        args = parser.parse_args()

        return args


def main_catch(func, args):
    try:
        func(args)

    except Exception as e:
        logger.error(e.message)
        sys.exit(-1)


def main(argv):
    args = Prepare().parser()
    main_catch(args.func, args)


def storage(args):
    try:
        logger.info("Benchmark storage cmd. ")
        result = Benchmark().sar_stats(args.d)
        result = result.write_json()
        # Write job passed flag
        sys.stdout.write(Benchmark().output_split_text)
        # Write output
        sys.stdout.write(result)

    except Exception as ex:
        logger.exception(ex.message)
        sys.exit(-1)
    sys.exit(0)


def client(args):
    try:
        logger.info("Benchmark client cmd. ")
        if args.m =="w":
            result = Benchmark().rados_benchmark(args.b,True,args.d,args.t,args.p)

        else:
            result = Benchmark().rados_benchmark(None,False,args.d,args.t,args.p)

        result = result.write_json()
        # Write job passed flag
        sys.stdout.write(Benchmark().output_split_text)
        # Write output
        sys.stdout.write(result)


    except Exception as ex:
        logger.exception(ex.message)
        sys.exit(-1)
    sys.exit(0)

def manager(args):
    try:

        logger.info("Benchmark manager cmd. ")
        clients =  args.c.split(',')
        if len(clients)<1:
            print "No clients set."
            sys.exit(-1)

        cleanup = True
        if args.cleanup == "0":
            cleanup = False

        result = Benchmark().manager(args.type,args.d,args.t,clients,args.p,cleanup)

        result = result.write_json()
        # Write job passed flag
        sys.stdout.write(Benchmark().output_split_text)
        # Write output
        sys.stdout.write(result)

    except Exception as ex:
        logger.exception(ex.message)
        sys.exit(-1)
    sys.exit(0)


def clean(args):
    try:
        logger.info("Benchmark clean cmd. ")
        pool = args.p
        CephAPI().rados_benchmark_clean(pool)

    except Exception as ex:
        logger.exception(ex.message)
        sys.exit(-1)
    sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])



