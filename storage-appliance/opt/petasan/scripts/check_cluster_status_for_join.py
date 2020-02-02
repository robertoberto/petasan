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
from PetaSAN.core.ceph.deploy.build import mon_status_check
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.log import logger


cluster_conf = configuration()
quorum_size = "0"
if cluster_conf.are_all_mgt_nodes_in_cluster_config():
    try:
        quorum_size = len(mon_status_check().get('quorum'))
        sys.stdout.write(str(quorum_size))

        if int(quorum_size) == 3:
            sys.exit(0) #  healthy cluster

    except Exception as ex:
        logger.error("Cluster not running")
        sys.stdout.write("-1")
        sys.exit(-1)

else:
    sys.stdout.write(quorum_size)
    sys.exit(0)

sys.exit(-1)

