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

import sys
from PetaSAN.backend.file_sync_manager import FileSyncManager

if len(sys.argv) != 2 :
	print('usage: sync_file  full_file_path')
	sys.exit(1)

path= sys.argv[1]
if FileSyncManager().commit_file(path):
	print('Success')

sys.exit(0)


