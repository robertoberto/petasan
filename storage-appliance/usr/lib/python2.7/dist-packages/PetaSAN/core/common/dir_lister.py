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

import os


class DirLister(object):
    FILES = 1
    FOLDERS = 2
    ALL = 3

    def __init__(self):
        pass

    def get_list(self, path, type, recursive = False):
        files_list = []
        folders_list = []
        dir_list = []
        if not recursive:
            for file in os.listdir(path):
                if os.path.isfile(os.path.join(path, file)):
                    files_list.append(os.path.join(path, file))
                else:
                    folders_list.append(os.path.join(path, file))
        else:
            # r=root, d=directories, f = files
            for r, d, f in os.walk(path):
                if type != self.FOLDERS:
                    for file in f:
                        files_list.append(os.path.join(r, file))
                if type != self.FILES:
                    for folder in d:
                        folders_list.append(os.path.join(r, folder))

        if type == self.FILES:
            dir_list = files_list
        elif type == self.FOLDERS:
            dir_list = folders_list
        elif type == self.ALL:
            dir_list = files_list + folders_list

        return dir_list


