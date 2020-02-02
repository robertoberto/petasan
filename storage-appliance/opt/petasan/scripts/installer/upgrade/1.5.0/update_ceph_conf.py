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

cfg = ConfigFileMgr()

cfg.add_option('global', 'mon_max_pg_per_osd', '300')
cfg.add_option('global', 'osd_max_pg_per_osd_hard_ratio', '2.5')
cfg.add_option('global', 'mon_osd_min_in_ratio', '0.3')
cfg.add_option('global', 'mon_allow_pool_delete', 'true')
cfg.add_option('global', 'bluestore_block_db_size', '21474836480')

#cfg.print_debug()
cfg.save_config_file()


