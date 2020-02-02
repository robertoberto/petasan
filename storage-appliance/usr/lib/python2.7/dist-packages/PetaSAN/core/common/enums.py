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

class ManageDiskStatus(object):
    data_missing = -1000
    is_busy = 11
    wrong_data = -10
    ip_out_of_range = -9
    disk_created_cant_start = -8
    wrong_subnet = -7
    used_already = -6
    disk_get__list_error = -5
    disk_meta_cant_read = -4
    disk_name_exists = -3
    disk_exists = -2
    error = -1
    done = 1
    done_metaNo = 2


class DisplayDiskStatus(object):
    started = 1
    stopped = 2
    unattached = 3
    stopping = 4
    starting = 5
    deleting = 6


class DeleteDiskStatus(object):
    error = -1
    done = 1


class Status(object):
    error = -1
    done = 1


class JoiningStatus(object):
    node_joined = 3

    one_node_exists = 1
    two_node_exist = 2
    not_joined = 0


class StopDiskStatus(object):
    working = -2
    error = -1
    done = 1


class NewIPValidation(object):
    invalid_count = -3
    wrong_subnet = -2
    used_already = -1
    valid = 1


class ManageUserStatus(object):
    not_exists = -3
    exists = -2
    error = -1
    done = 1


class PagesName():
    add_disk_page_name = "AddDisk"
    disk_list_page_name = "DiskList"
    network_configuration_page_name = "NetworkConfiguration"
    disk_configuration_page_name = "DiskConfiguration"

    bucket_tree = "BucketTree"
    rules_list = "RulesList"
    pool_list = "PoolsList"
    ec_profiles_list = "ProfilesList"
    replication_users = "ReplicationUsers"

    # Eng Doaa Test : new page_url
    backup_disk = "BackupDisk"
    test = "test"


class RolesName():
    administrator_role_name = "Administrator"
    viewer_role_name = 'Viewer'


class BuildStatus():
    connection_error = -5
    build_consul_error = -4
    build_osd_error = -3
    build_monitors_error = -2
    error = -1
    done = 1
    OneManagementNode = 2
    TwoManagementNodes = 3
    joined = 4
    done_joined = 5
    done_replace = 6


class PathType:
    iscsi_subnet1 = 1
    iscsi_subnet2 = 2
    both = 3


class NodeStatus:
    down = 0
    up = 1


class OsdStatus:
    no_status = -1
    down = 0
    up = 1
    adding = 2
    deleting = 3
    adding_journal = 4
    adding_cache = 5


class DiskUsage:
    no = -1
    osd = 0
    system = 1
    mounted = 2
    journal = 3
    cache = 4


class DeleteNodeStatus:
    not_allow = -2
    error = -1
    done = 1


class BondMode:
    balance_rr = "balance-rr"
    active_backup = "active-backup"
    balance_xor = "balance-xor"
    broadcast = "broadcast"
    mode_802_3_ad = "802.3ad (LACP)"
    balance_tlb = "balance-tlb"
    balance_alb = "balance-alb"


class REPLICASSAVESTATUS:
    min_size_wrn = -2
    error = -1
    done = 1


class TestModes:
    four_k = "4k"
    four_m = "4m"


class TestTypes:
    read = "read"
    write = "write"
    sync_write = "sync_write"
    random_write = "randwrite"
    random_read = "randread"


class SarOutputProperties(object):
    cpu_CPU = "CPU"
    cpu_user = "%user"
    cpu_nice = "%nice"
    cpu_system = "%system"
    cpu_iowait = "%iowait"
    cpu_steal = "%steal"
    cpu_idle = "%idle"

    ram_kbmemfree = "kbmemfree"
    ram_kbavail = "kbavail"
    ram_kbmemused = "kbmemused"
    ram_memused = "%memused"
    ram_kbbuffers = "kbbuffers"
    ram_kbcached = "kbcached"
    ram_kbcommit = "kbcommit"
    ram_commit = "%commit"
    ram_kbactive = "kbactive"
    ram_kbinact = "kbinact"
    ram_kbdirty = "kbdirty"

    disk_DEV = "DEV"
    disk_tps = "tps"
    disk_rkB = "rkB/s"
    disk_wkB = "wkB/s"
    disk_areq_sz = "areq-sz"
    disk_aqu_sz = "aqu-sz"
    disk_await = "await"
    disk_svctm = "svctm"
    disk_util = "%util"

    iface_IFACE = "IFACE"
    iface_rxpck = "rxpck/s"
    iface_txpck = "txpck/s"
    iface_rxkB = "rxkB/s"
    iface_txkB = "txkB/s"
    iface_rxcmp = "rxcmp/s"
    iface_txcmp = "txcmp/s"
    iface_rxmcst = "rxmcst/s"
    iface_ifutil = "%ifutil"


class BlockSize(object):
    four_mg = '4194304'
    four_kb = '4096'


class RadosBenchmarkType(object):
    four_mg_Throughput = 1
    four_kb_iops = 2


class EmailSecurity(object):
    ssl = 1
    tls = 2
    plain = 3
    anonymous = 4


class MaintenanceMode(object):
    enable = 1
    disable = 0


class MaintenanceConfigState(object):
    on = 1
    off = 0


class ReassignPathStatus(object):
    failed = 3
    succeeded = 2
    pending = 1
    moving = 0


class CompressionMode(object):
    none = 1
    force = 2


class CompressionAlgorithm(object):
    none = 1
    zlib = 2
    snappy = 3
    zstd = 4
    lz4 = 5


class DiskSmartHealth(object):
    passed = 'PASSED'
    failed = 'FAILED'
    unknown = 'UNKNOWN'


class CacheType(object):
    dm_cache = 'dmcache'
    dm_writecache = 'writecache'

