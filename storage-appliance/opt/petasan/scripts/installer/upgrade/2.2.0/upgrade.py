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


from PetaSAN.core.common.config_file_mgr import ConfigFileMgr



# update ceph config file

cfg = ConfigFileMgr()

# deprectated in favor of osd_memory_target
cfg.remove_option('osd','bluestore_cache_size_hdd')
cfg.remove_option('osd','bluestore_cache_size_ssd')

# for upgrades reduce osd_memory_target to 2G (default is 4G) 
#cfg.add_option('osd','osd_memory_target','4294967296')
cfg.add_option('osd','osd_memory_target','2147483648')

cfg.add_option('osd','osd_snap_trim_sleep','0.1')


cfg.save_config_file()


