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
from PetaSAN.core.cluster.configuration import configuration
from flask import json


# add vlan to cluster_info.json

config = configuration()
cluster_info = config.get_cluster_info()

if not hasattr(cluster_info,'backend_1_vlan_id'):
    cluster_info.backend_1_vlan_id = ""
if not hasattr(cluster_info,'backend_2_vlan_id'):
    cluster_info.backend_2_vlan_id = ""

config.set_cluster_network_info(cluster_info)


# update ceph config file

cfg = ConfigFileMgr()

cfg.add_option('global','bluestore_block_db_size','64424509440')

cfg.remove_option('osd','osd_op_threads')
cfg.add_option('osd','osd_op_num_shards_hdd','5')
cfg.add_option('osd','osd_op_num_shards_ssd','8')
cfg.add_option('osd','osd_op_num_threads_per_shard_hdd','1')
cfg.add_option('osd','osd_op_num_threads_per_shard_ssd','2')

cfg.add_option('osd','bluestore_prefer_deferred_size_hdd','32768')
cfg.add_option('osd','bluestore_prefer_deferred_size_ssd','0')

cfg.add_option('osd','bluestore_cache_size_hdd','1073741824')
cfg.add_option('osd','bluestore_cache_size_ssd','3221225472')

cfg.save_config_file()


# lio tunings

try :
    lio_tuning = {}
    lio_tuning_path = '/opt/petasan/config/tuning/current/lio_tunings'

    with open(lio_tuning_path, 'r') as f:
        lio_tuning = json.load(f)

    lio_tuning['targets'][0]['tpgs'][0]['parameters']['FirstBurstLength'] = '1048576'
    lio_tuning['targets'][0]['tpgs'][0]['parameters']['MaxBurstLength'] = '1048576'
    lio_tuning['targets'][0]['tpgs'][0]['parameters']['MaxOutstandingR2T'] = '16'
    lio_tuning['targets'][0]['tpgs'][0]['parameters']['MaxRecvDataSegmentLength'] = '1048576'
    lio_tuning['targets'][0]['tpgs'][0]['parameters']['MaxXmitDataSegmentLength'] = '1048576'

    with open(lio_tuning_path, 'w') as f:
        s = json.dumps(lio_tuning,indent=4, sort_keys=True)
        f.write(s)

except :
    pass

