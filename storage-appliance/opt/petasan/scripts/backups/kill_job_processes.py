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

from PetaSAN.backend.replication.replication_handler import ReplicationHandler
import argparse
import sys
from PetaSAN.core.common.log import logger


def run(args):
    active_job_id = str(args.active_job_id)

    try:
        rep_handler = ReplicationHandler()
        rep_handler.kill_job_processes(active_job_id)
        print("replication job processes has been killed.")
        sys.exit(0)
    except:
        sys.exit(-1)



def main():
    parser = argparse.ArgumentParser(description="This is a script that will kill all active job processes.")

    parser.add_argument("--active_job_id",
                        help="active replication job id",
                        required=True)

    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
    sys.exit(0)

