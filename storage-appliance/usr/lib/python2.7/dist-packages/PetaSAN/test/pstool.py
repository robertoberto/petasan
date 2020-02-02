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
from time import sleep
import uuid
from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.enums import PathType, DisplayDiskStatus
from PetaSAN.core.entity.disk_info import DiskMeta
import subprocess


class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=True)
        subparser = parser.add_subparsers()
        sub_add_disk = subparser.add_parser('add-disk')
        sub_add_disk.set_defaults(func=add_disk)
        sub_add_disk.add_argument(
            '-n',
            help='Number of disks you need to create.', required=True
        )
        sub_add_disk.add_argument(
            '-s',
            help='Disk size.', required=True
        )
        sub_add_disk.add_argument(
            '-p',
            help='paths count.', required=True
        )


        sub_stop_all = subparser.add_parser('stop-all')
        sub_stop_all.set_defaults(func=stop_all)
        sub_stop_all.add_argument(
            '-a',
            help='Stop auto only 1 or 0 stop all.default 1 ', default=1
        )
        sub_stop_all.add_argument(
            '-w',
            help='Display wait message until all disks started.default 1 ', default=1
        )

        sub_start_all = subparser.add_parser('start-all')
        sub_start_all.set_defaults(func=start_all)
        sub_start_all.add_argument(
            '-a',
            help='Start auto only 1 or 0 start all.', default=1
        )

        sub_start_all.add_argument(
            '-w',
            help='Display wait message until all disks started.default 1 ', default=1
        )


        sub_delete_all = subparser.add_parser('delete-all')
        sub_delete_all.set_defaults(func=delete_all)
        sub_delete_all.add_argument(
            '-a',
            help='Delete auto only 1 or 0 delete all.default 1 ', default=1
        )

        sub_delete_all.add_argument(
            '-w',
            help='Display wait message until all disks deleted. ', default=1
        )

        sub_test_env = subparser.add_parser('build-test-env')
        sub_test_env.set_defaults(func=build_test_env)

        sub_delete_env = subparser.add_parser('delete-test-env')
        sub_delete_env.set_defaults(func=delete_test_env)


        sub_stress = subparser.add_parser('stress')
        sub_stress.set_defaults(func=stress)
        sub_stress.add_argument(
            '-time',
            help='Time of test in sec, default 10.', default=10
        )

        sub_stress.add_argument(
            '-io',
            help='Number of threads, default 16.', default=16
        )

        sub_stress.add_argument(
            '-size',
            help='Size of data will use in test, default 4K .With write or all. ', default=4069
        )

        sub_stress.add_argument(
            '-t',
            help='Type 0 all ,1 write,2 rand and 3 seq, default 0 . ', default=0
        )

        args = parser.parse_args()

        return args


def main_catch(func, args):
    try:
        func(args)

    except Exception as e:
        print (e.message)
        print("Error while run command.")


def main(argv):
    args = Prepare().parser()
    main_catch(args.func, args)


def add_disk(args):
    md=ManageDisk()
    for i in range(0,int(args.n)):
        disk_meta = DiskMeta()
        disk_meta.disk_name = "auto "+str(uuid.uuid4()).replace("-"," ")
        disk_meta.size = int(args.s)
        status = md.add_disk(disk_meta,None,PathType.both,int(args.p))
        if status >0:
            print "Disk number {} is created".format(i)
        else:
            print "Disk number {} can not create, status error is {}.".format(i,status)


def stop_all(args):
    md=ManageDisk()
    for d in md.get_disks_meta():
        if int(args.a) == 1:
            if str(d.disk_name).startswith("auto "):
                md.stop(d.id)
        else:
            md.stop(d.id)
    if int(args.w) == 0:
        return
    status = False
    while status != True:
        not_complete = False
        for d in md.get_disks_meta():
            if int(args.a) == 1:
                if str(d.disk_name).startswith("auto "):
                   if d.status != DisplayDiskStatus.stopped:
                       print "wait please."
                       not_complete = True
                       sleep(10)
                       break
            else:
                if d.status != DisplayDiskStatus.stopped:
                       print "wait please."
                       not_complete = True
                       sleep(10)
                       break
        if not not_complete:
            status = True
    print "All disks stopped."

def start_all(args):
    md=ManageDisk()
    for d in md.get_disks_meta():
        if int(args.a) == 1:
            if str(d.disk_name).startswith("auto "):
                md.start(d.id)
        else:
            md.start(d.id)

    if int(args.w) == 0:
        return
    status = False
    while status != True:
        not_complete = False
        for d in md.get_disks_meta():
            if int(args.a) == 1:
                if str(d.disk_name).startswith("auto "):
                   if d.status != DisplayDiskStatus.started:
                       print "wait please."
                       not_complete = True
                       sleep(10)
                       break
            else:
                if d.status != DisplayDiskStatus.started:
                       print "wait please."
                       not_complete = True
                       sleep(10)
                       break
        if not not_complete:
            status = True
    print "All disks started."

def delete_all(args):
    md=ManageDisk()
    for d in md.get_disks_meta():
        if int(args.a) == 1:
            if str(d.disk_name).startswith("auto "):
                md.delete_disk(d.id)
        else:
            md.delete_disk(d.id)

    status = False
    while status != True:
        not_complete = False
        for d in md.get_disks_meta():
            if int(args.a) == 1:
                if str(d.disk_name).startswith("auto "):
                   print "wait please."
                   not_complete = True
                   sleep(10)
                   break
            else:

               print "wait please."
               not_complete = True
               sleep(10)
               break
        if not not_complete:
            status = True
def build_test_env(args):
    proc = subprocess.Popen(['ceph osd pool create test 1000 replicated=3'],shell=True,stdout=subprocess.PIPE)

    while True:
      line = proc.stdout.readline()
      if line != '':
        #the real code does filtering here
        print "Build:", line.rstrip()
      else:
        break

def delete_test_env(args):

    proc = subprocess.Popen(['ceph osd pool delete test test --yes-i-really-really-mean-it'],shell=True,stdout=subprocess.PIPE)

    while True:
      line = proc.stdout.readline()
      if line != '':
        #the real code does filtering here
        print "Delete :", line.rstrip()
      else:
        break

def stress(args):
    test_type = int(args.t)
    if test_type == 0 or test_type == 1:
        print "################ start write test #######################"
        proc = subprocess.Popen(['rados bench -p test {} write -t {} -b {} --no-cleanup'.format(args.time,args.io,args.size)]
                                ,shell=True,stdout=subprocess.PIPE)
        while True:
          line = proc.stdout.readline()
          if line != '':
            #the real code does filtering here
            print "Stress :", line.rstrip()
          else:
            break
    if test_type == 0 or test_type == 2:
        print "################ start rand test #######################"
        proc = subprocess.Popen(['rados bench -p test {} rand -t {} '.format(args.time,args.io)]
                                ,shell=True,stdout=subprocess.PIPE)
        while True:
          line = proc.stdout.readline()
          if line != '':
            #the real code does filtering here
            print "Stress :", line.rstrip()
          else:
            break
    if test_type == 0 or test_type == 3:
        print "################ start seq test #######################"
        proc = subprocess.Popen(['rados bench -p test {} seq -t {} '.format(args.time,args.io)]
                                ,shell=True,stdout=subprocess.PIPE)
        while True:
          line = proc.stdout.readline()
          if line != '':
            #the real code does filtering here
            print "Stress :", line.rstrip()
          else:
            break
if __name__ == '__main__':
   main(sys.argv[1:])



