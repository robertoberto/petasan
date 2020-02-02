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

from PetaSAN.core.common.enums import MaintenanceMode, MaintenanceConfigState
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.maintenance import MaintenanceStatus, MaintenanceConfig


class ManageMaintenance:
    def __init__(self):
        pass

    def get_maintenance_config(self):
        api = ConfigAPI()
        maintenance = CephAPI().get_maintenance_setting()
        maintenance.fencing = api.read_maintenance_config().fencing
        return maintenance

    def set_maintenance_config(self, maintenance_config):
        """

        :type maintenance_config: MaintenanceConfig
        """
        CephAPI().set_maintenance_setting(maintenance_config)
        api = ConfigAPI()
        maintenance  = MaintenanceConfig()
        maintenance.fencing = maintenance_config.fencing
        api.write_maintenance_config(maintenance)

    def get_maintenance_mode(self):
        for key,val in self.get_maintenance_config().__dict__.iteritems():
            if val == MaintenanceConfigState.off:
                return MaintenanceMode.enable
        return MaintenanceMode.disable

    def set_backfill_speed(self, backfill_speed):
        ceph_api = CephAPI()
        ceph_api.set_backfill_speed(backfill_speed)

