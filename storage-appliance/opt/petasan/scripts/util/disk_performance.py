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

from flask import json
from PetaSAN.core.common.messages import gettext
from PetaSAN.core.common.cmd import *
from PetaSAN.core.common.enums import TestModes, TestTypes
import argparse
import sys
from PetaSAN.core.common.log import logger


class Prepare(object):
    @staticmethod
    def parser():
        parser = argparse.ArgumentParser(add_help=False)
        parser.set_defaults(func=check_disk_performance)
        parser.add_argument('-disk_name')
        parser.add_argument('-threads_no')

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


def check_disk_performance(args):
    try:
        disk_name = args.disk_name
        threads_no = args.threads_no
        test_modes = []
        test_modes.append(TestModes.four_k)
        test_modes.append(TestModes.four_m)

        test_types = []
        test_types.append(TestTypes.read)
        test_types.append(TestTypes.write)
        test_types.append(TestTypes.sync_write)
        test_types.append(TestTypes.random_read)
        test_types.append(TestTypes.random_write)
        for mode in test_modes:
            for type in test_types:
                cmd = "fio --name={} --filename=/dev/{} --iodepth=1 --rw={} --bs={} " \
                      "--direct=1 --runtime=20 --time_based --numjobs={} --group_reporting --output-format=json"
                if type == TestTypes.read:
                    test_name = gettext(mode + "_sequential_read")
                    cmd = cmd.format(
                        test_name, disk_name, type, mode, threads_no)
                elif type == TestTypes.write:
                    test_name = gettext(mode + "_sequential_write")
                    cmd = cmd.format(
                        test_name, disk_name, type, mode, threads_no)
                elif type == TestTypes.sync_write:
                    test_name = gettext(mode + "_sequential_write_sync")
                    type = TestTypes.write
                    cmd = cmd.format(
                        test_name, disk_name, type, mode, threads_no) + ' --sync=1'
                elif type == TestTypes.random_read:
                    test_name = gettext(mode + "_random_read")
                    cmd = cmd.format(
                        test_name, disk_name, type, mode, threads_no)
                    type = TestTypes.read
                elif type == TestTypes.random_write:
                    test_name = gettext(mode + "_random_write")
                    cmd = cmd.format(
                        test_name, disk_name, type, mode, threads_no)
                    type = TestTypes.write
                call_cmd("sync")
                call_cmd("echo 3 > /proc/sys/vm/drop_caches")
                out, err = exec_command(cmd)
                print_results(out, type, mode, disk_name, threads_no)
    except Exception as e:
        print e

    sys.exit(0)


def print_results(data, type, mode, disk_name, threads_no):
    sys.stdout.flush()
    output = json.loads(data)
    test_name = output['jobs'][0]['jobname'].replace("_", " ")
    if mode == TestModes.four_k:
        value = output['jobs'][0][type]['iops']
        print gettext("4k_test_result_message").format(disk_name, test_name, threads_no, int(value))
    elif mode == TestModes.four_m:
        value = output['jobs'][0][type]['bw'] * 1024
        if value <= 1024:
            value = str(value) + ' B/s'
        elif value <= (1024 * 1024):
            value = str((value / 1024)) + ' KB/s'
        elif value <= (1024 * 1024 * 1024):
            value = str(((value / 1024) / 1024)) + ' MB/s'
        elif value <= (1024 * 1024 * 1024 * 1024):
            value = str((((value / 1024) / 1024) / 1024)) + ' GB/s'
        print gettext("4m_test_result_message").format(disk_name, test_name, threads_no, value)

    sleep(1)


if __name__ == '__main__':
    main(sys.argv[1:])
