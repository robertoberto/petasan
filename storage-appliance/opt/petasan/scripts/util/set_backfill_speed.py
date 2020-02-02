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
from PetaSAN.core.common.log import logger
from PetaSAN.core.common.cmd import call_cmd, exec_command, exec_command_ex


def run(args):
    value = int(args.value)
    cluster_name = configuration().get_cluster_name()

    if value == 1:
        print('backfill_speed choice : very slow')
        ret1, stdout1, stderr1 = exec_command_ex("ceph tell osd.* injectargs '--osd_max_backfills 1' --cluster " + cluster_name)
        ret2, stdout2, stderr2 = exec_command_ex("ceph tell osd.* injectargs '--osd_recovery_max_active 1' --cluster " + cluster_name)
        ret3, stdout3, stderr3 = exec_command_ex("ceph tell osd.* injectargs '--osd_recovery_sleep 2' --cluster " + cluster_name)
        print('Done changing backfill speed to very slow ...')

    elif value == 2:
        print('backfill_speed choice : slow')
        ret1, stdout1, stderr1 = exec_command_ex("ceph tell osd.* injectargs '--osd_max_backfills 1' --cluster " + cluster_name)
        ret2, stdout2, stderr2 = exec_command_ex("ceph tell osd.* injectargs '--osd_recovery_max_active 1' --cluster " + cluster_name)
        ret3, stdout3, stderr3 = exec_command_ex("ceph tell osd.* injectargs '--osd_recovery_sleep 0.7' --cluster " + cluster_name)
        print('Done changing backfill speed to slow ...')

    elif value == 3:
        print('backfill_speed choice : medium')
        ret1, stdout1, stderr1 = exec_command_ex("ceph tell osd.* injectargs '--osd_max_backfills 1' --cluster " + cluster_name)
        ret2, stdout2, stderr2 = exec_command_ex("ceph tell osd.* injectargs '--osd_recovery_max_active 1' --cluster " + cluster_name)
        ret3, stdout3, stderr3 = exec_command_ex("ceph tell osd.* injectargs '--osd_recovery_sleep 0' --cluster " + cluster_name)
        print('Done changing backfill speed to medium ...')

    elif value == 4:
        print('backfill_speed choice : fast')
        ret1, stdout1, stderr1 = exec_command_ex("ceph tell osd.* injectargs '--osd_max_backfills 5' --cluster " + cluster_name)
        ret2, stdout2, stderr2 = exec_command_ex("ceph tell osd.* injectargs '--osd_recovery_max_active 3' --cluster " + cluster_name)
        ret3, stdout3, stderr3 = exec_command_ex("ceph tell osd.* injectargs '--osd_recovery_sleep 0' --cluster " + cluster_name)
        print('Done changing backfill speed to fast ...')

    elif value == 5:
        print('backfill_speed choice : very fast')
        ret1, stdout1, stderr1 = exec_command_ex("ceph tell osd.* injectargs '--osd_max_backfills 7' --cluster " + cluster_name)
        ret2, stdout2, stderr2 = exec_command_ex("ceph tell osd.* injectargs '--osd_recovery_max_active 7' --cluster " + cluster_name)
        ret3, stdout3, stderr3 = exec_command_ex("ceph tell osd.* injectargs '--osd_recovery_sleep 0' --cluster " + cluster_name)
        print('Done changing backfill speed to very fast ...')

    else:
        print("error : failed to set speed value : No such value {}".format(value))

    return



def main():
    parser = argparse.ArgumentParser(description="This is a script that will set the new backfill speed.")
    parser.add_argument("-value",
                        help="value of backfill speed : 1 for Very Slow, 2 for Slow, 3 for Medium, 4 for Fast, 5 for Very Fast",
                        required=True)

    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
    sys.exit(0)

