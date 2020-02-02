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

from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.cmd import call_cmd
from PetaSAN.core.common.dir_lister import DirLister
from PetaSAN.core.common.log import logger
import sys
import os

def main():
    shared_dir_stat = '/opt/petasan/config/shared/graphite/whisper/PetaSAN/ClusterStats/'
    config = configuration()
    custom_cluster_name = config.get_cluster_name(custom_name=True)
    cluster_name = "ceph"

    if custom_cluster_name is not cluster_name:
        process_path(shared_dir_stat, custom_cluster_name, cluster_name)

    sys.exit(0)



def process_path(path, custom_cluster_name, cluster_name):
    dir_lister = DirLister()
    files_list = dir_lister.get_list(path, dir_lister.FILES, recursive=True)
    for file in files_list:
        if custom_cluster_name in file.split("/")[-1] and os.path.exists(file):
            status = change_path_name(file, custom_cluster_name, cluster_name)
    folders_list = dir_lister.get_list(path, dir_lister.FOLDERS, recursive=True)
    folders_list = sorted(folders_list, key=len, reverse=True)
    for dir in folders_list:
        if custom_cluster_name in dir.split("/")[-1] and os.path.isdir(dir):
            status = change_path_name(dir, custom_cluster_name, cluster_name)



def change_path_name(path, old_name, new_name):

    last_dir = path.split("/")[-1]
    updated_last_dir = last_dir.replace(old_name, new_name)
    new_path = path.replace(last_dir, updated_last_dir)
    stat = call_cmd("mv {} {}".format(path, new_path))

    if not stat:
        logger.error("Can't change path from {} to {}".format(path, new_path))

    return stat




if __name__ == '__main__':
    main()
