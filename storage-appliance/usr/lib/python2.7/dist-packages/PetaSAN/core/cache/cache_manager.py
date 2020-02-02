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

from PetaSAN.core.common.enums import CacheType
from PetaSAN.core.cache.cache import *
from PetaSAN.core.lvm import lvm_lib


class CacheManager(object):
    def __init__(self):
        pass

    def create(self, origin_disk, cache_disk, cache_type):
        """
        # Build caching between origin disk and cache disk depending on the type of cache used ...
        """
        if cache_type == CacheType.dm_writecache:
            wc = WriteCache()
            return wc.create(origin_disk, cache_disk)

        elif cache_type == CacheType.dm_cache:
            dmc = DMCache()
            return dmc.create(origin_disk, cache_disk)

    def activate(self):
        """
        # Activating Cache depending on the type of cache used ...
        """
        # Activating wirtecache
        wc = WriteCache()
        wc.activate()

        dmc = DMCache()
        dmc.activate()

    def delete(self, origin_disk, cache_type):
        """
        # Remove caching between origin disk and cache disk depending on the type of cache used ...
        """
        if cache_type == CacheType.dm_writecache:
            wc = WriteCache()
            wc.delete(origin_disk)

        elif cache_type == CacheType.dm_cache:
            dmc = DMCache()
            dmc.delete(origin_disk)

    def get_cache_type(self, origin_disk):
        """
        # This function returns None, DMCache, WriteCache, BCache, ... etc ...
        """
        devices = self.get_physical_devices(origin_disk)

        if devices[CacheType.dm_cache]:
            return CacheType.dm_cache

        elif devices[CacheType.dm_writecache]:
            return CacheType.dm_writecache

        else:
            return None

    def get_physical_devices(self, origin_disk):
        """
        # Get physical devices that linked to the vg of the origin disk ...
        """
        cache = Cache()
        vg_name = cache.get_vg_by_disk(origin_disk)
        physical_disks = lvm_lib.get_physical_disks(vg_name)
        return physical_disks

    def is_cached(self, origin_disk):
        """
        # Check if origin disk is related to cache device or not ...
        """
        devices = self.get_physical_devices(origin_disk)

        if devices[CacheType.dm_cache] or devices[CacheType.dm_writecache]:
            return True
        else:
            return False

#  ##=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###=###  #

