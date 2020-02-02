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
from PetaSAN.core.common.log import logger
from PetaSAN.core.entity.network import Bond
from PetaSAN.core.cluster.configuration import configuration
from flask import json


class old_Bond(object):
    def __init__(self):
        self.name = ""
        self.primary_eth_name = ""
        self.other_eths_names = []
        self.mode = ""
        self.is_jumbo_frames = False

    def load_json(self, j):
        self.__dict__ = json.loads(j)


def set_cluster_interface(bonds=[]):
    if (bonds == None or len(bonds) == 0):
        return
    config = configuration()
    cluster_info = config.get_cluster_info()

    cluster_info.bonds = bonds
    config.set_cluster_network_info(cluster_info)
    logger.info("Updated cluster bonds to 1.3 successfully.")


try:
    old_bonds = configuration().get_cluster_bonds()
    new_bonds = []
    if len(old_bonds) > 0:
        for ob in old_bonds:
            if not hasattr(ob, "primary_eth_name"):
                sys.exit(0)
                break

            bond = Bond()
            bond.is_jumbo_frames = ob.is_jumbo_frames
            bond.mode = ob.mode
            bond.name = ob.name
            bond.interfaces = ob.primary_eth_name + "," + ob.other_eths_names
            bond.primary_interface = ob.primary_eth_name
            new_bonds.append(bond)

        if len(old_bonds) == len(new_bonds):
            set_cluster_interface(new_bonds)
        else:
            sys.exit(-1)
except Exception as ex:
    logger.exception(ex.message)
    sys.exit(-1)
sys.exit(0)

