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
import subprocess
import time
import re
import stat
import tempfile
import uuid
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.cmd import exec_command, call_cmd, exec_command_ex
from PetaSAN.core.common.log import logger


PTYPE = {

    'journal': '45b0969e-9b03-4f30-b4c6-b4b80ceff106',

    'block': 'cafecafe-9b03-4f30-b4c6-b4b80ceff106',

    'block.db': '30cd0809-c2b2-499c-8879-2d6b78529876',

    'osd': '4fbd7e29-9d25-41b8-afd0-062c0ceff05d',

    'cache': 'f7e357a6-a096-4498-93c1-0ff812402190'

}

STATEDIR = '/var/lib/ceph'
SYSFS = '/sys'
DEFAULT_FS_TYPE = 'xfs'
PROCDIR = '/proc'
BLOCKDIR = '/sys/block'
ROOTGROUP = 'root'
SYSCONFDIR = '/etc/ceph'


class Ptype(object):

    @staticmethod
    def is_regular_space(ptype):
        return Ptype.is_what_space(ptype)

    @staticmethod
    def is_what_space(ptype):
        for name in Space.NAMES:
            if ptype == PTYPE[name]:
                return True
        return False

    @staticmethod
    def space_ptype_to_name(ptype):
        for name in Space.NAMES:
            if ptype == PTYPE[name]:
                return name
        raise ValueError('ptype ' + ptype + ' not found')


class Space(object):
    NAMES = ('block', 'journal', 'block.db')


def probe_part(disk_name):
    # step 1 call pertprobe
    logger.info('Calling partprobe on %s device', disk_name)
    dev = "/dev/" + disk_name
    cmd = 'partprobe ' + dev
    logger.info('Executing ' + cmd)
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)

    # step 2 call udev events
    logger.info('Calling udevadm on %s device', disk_name)
    cmd = 'udevadm settle --timeout 30'
    logger.info('Executing ' + cmd)
    if not call_cmd(cmd):
        logger.error('Error executing ' + cmd)
    time.sleep(3)


def create_partition(disk_name, name, size, uuid, ptype=None):
    try:

        path = "/dev/" + disk_name
        num = get_next_partition_index(dev=path)
        new = ' --new={num}:0:+{size}M'.format(num=num, size=size)
        logger.info('Creating %s partition num %d size %d on %s',
                    name, num, size, path)
        cmd = '/sbin/sgdisk' + new
        cmd += ' --change-name={num}:ceph-{name}'.format(num=num, name=name)
        cmd += ' --partition-guid={num}:{uuid}'.format(num=num, uuid=uuid)
        if ptype is not None:
            cmd += ' --typecode={num}:{uuid}'.format(num=num, uuid=ptype)
        cmd += ' --mbrtogpt -- ' + path
        ret = subprocess.call(cmd.split())
        if ret == 0:
            probe_part(disk_name)
            return num

    except Exception as e:
        logger.error(e)

        return False


def create_journal_partition(disk_name, external=True):
    try:
        uuid1 = uuid.uuid4()
        journal_size = get_journal_size()
        size = int(journal_size) / (1024 * 1024)
        ptype = None
        name = "journal"
        if external:
            ptype = PTYPE['block.db']
            # name = "block.db"
            name = "journal-db"
        part_num = create_partition(disk_name, name, size, uuid1, ptype)
        return part_num
    except Exception as e:
        logger.error("creating journal partition failed ", e)
        return None


def create_osd_partition(disk_name):
    try:
        uuid1 = uuid.uuid4()
        size = 0
        ptype = None
        name = "data"
        part_num = create_partition(disk_name, name, size, uuid1, ptype)
        return part_num
    except Exception as e:
        logger.error("creating journal partition failed ", e)
        return False


def get_next_partition_index(dev):
    """
    Get the next free partition index on a given device.

    :return: Index number (> 1 if there is already a partition on the device)
    or 1 if there is no partition table.
    """
    try:
        output, err = exec_command('parted --machine -- {} print'.format(dev))
        lines = output
    except subprocess.CalledProcessError as e:
        logger.info('cannot read partition index; assume it '
                    'isn\'t present\n (Error: %s)' % e)
        return 1

    if not lines:
        raise logger.error('parted failed to output anything')
    logger.debug('get_free_partition_index: analyzing ' + lines)
    if ('CHS;' not in lines and
                'CYL;' not in lines and
                'BYT;' not in lines):
        raise logger.error('parted output expected to contain one of ' +
                           'CHH; CYL; or BYT; : ' + lines)
    if os.path.realpath(dev) not in lines:
        raise logger.error('parted output expected to contain ' + dev + ': ' + lines)
    _, partitions = lines.split(os.path.realpath(dev))
    numbers_as_strings = re.findall('^\d+', partitions, re.MULTILINE)
    partition_numbers = map(int, numbers_as_strings)
    if partition_numbers:
        return max(partition_numbers) + 1
    else:
        return 1


def get_dev_size(dev, size='megabytes'):
    fd = os.open(dev, os.O_RDONLY)
    dividers = {'bytes': 1, 'megabytes': 1024 * 1024}
    try:
        device_size = os.lseek(fd, 0, os.SEEK_END)
        divider = dividers.get(size, 1024 * 1024)  # default to megabytes
        return device_size // divider
    except Exception as error:
        logger.warning('failed to get size of %s: %s' % (dev, str(error)))
    finally:
        os.close(fd)


def list_all_partitions():
    """
    Return a list of devices and partitions
    """
    # first change is to set FREEBSD statically with false
    dev_part_list = {}
    names = os.listdir(BLOCKDIR)
    for name in names:
        # /dev/fd0 may hang http://tracker.ceph.com/issues/6827
        if re.match(r'^fd\d$', name):
            continue
        if not os.path.exists(get_dev_path(name)):
            logger.info("list_all_partitions() found unmapped device " + name)
            continue
        dev_part_list[name] = list_partitions(get_dev_path(name))
    return dev_part_list


def list_partitions(dev):
    dev = os.path.realpath(dev)
    return list_partitions_device(dev)


def block_path(dev):
    path = os.path.realpath(dev)
    rdev = os.stat(path).st_rdev
    (M, m) = (os.major(rdev), os.minor(rdev))
    return "{sysfs}/dev/block/{M}:{m}".format(sysfs=SYSFS, M=M, m=m)


def list_partitions_device(dev):
    """
    Return a list of partitions on the given device name
    """
    partitions = []
    basename = get_dev_name(dev)
    for name in os.listdir(block_path(dev)):
        if name.startswith(basename):
            partitions.append(name)
    return partitions


def get_dev_name(path):
    """
    get device name from path.  e.g.::

        /dev/sda -> sda, /dev/cciss/c0d1 -> cciss!c0d1

    a device "name" is something like::

        sdb
        cciss!c0d1

    """
    assert path.startswith('/dev/')
    base = path[5:]
    return base.replace('/', '!')


def get_dev_path(name):
    """
    get a path (/dev/...) from a name (cciss!c0d1)
    a device "path" is something like::

        /dev/sdb
        /dev/cciss/c0d1

    """
    return '/dev/' + name.replace('!', '/')


def get_partition_uuid(part):
    return get_blkid_partition_info(part, 'ID_PART_ENTRY_UUID')


def get_partition_type(part):
    return get_blkid_partition_info(part, 'ID_PART_ENTRY_TYPE')


def get_blkid_partition_info(part_name, what=None):
    dev = '/dev/' + part_name
    out, err = exec_command('blkid -o udev -p ' + dev)
    p = {}
    for line in out.splitlines():
        (key, value) = line.split('=')
        p[key] = value
    if what:
        return p.get(what)
    else:
        return p


def get_dev_fs(dev):
    out, err = exec_command('blkid -s TYPE ' + dev)
    if 'TYPE' in out:
        fstype = out.split()[1].split('"')[1]
        return fstype
    return None


def get_conf(cluster, variable):
    """
    Get the value of the given configuration variable from the
    cluster.

    :raises: Error if call to ceph-conf fails.
    :return: The variable value or None.
    """
    try:
        cmd = 'ceph-conf --cluster=' + cluster + ' --name=osd. --lookup ' + variable
        ret, out, err = exec_command_ex(cmd)
    except OSError as e:
        raise logger.error('error executing ceph-conf', e, err)
    if ret == 1:
        # config entry not found
        return None
    elif ret != 0:
        raise logger.error('getting variable from configuration failed')
    value = out.split('\n', 1)[0]
    # don't differentiate between "var=" and no var set
    if not value:
        return None
    return value


def mount(
        dev,
        fstype,
        options,
):
    """
    Mounts a device with given filessystem type and
    mount options to a tempfile path under /var/lib/ceph/tmp.
    """
    # sanity check: none of the arguments are None
    if dev is None:
        raise ValueError('dev may not be None')
    if fstype is None:
        raise ValueError('fstype may not be None')

    # pick best-of-breed mount options based on fs type
    if options is None:
        options = "noatime"

    myTemp = STATEDIR + '/tmp'
    # mkdtemp expect 'dir' to be existing on the system
    # Let's be sure it's always the case
    if not os.path.exists(myTemp):
        os.makedirs(myTemp)

    # mount
    path = tempfile.mkdtemp(
        prefix='mnt.',
        dir=myTemp,
    )
    try:
        logger.debug('Mounting %s on %s with options %s', dev, path, options)
        cmd = 'mount -t ' + fstype + '-o ' + options + ' -- ' + dev + ' ' + path
        exec_command_ex(cmd)

        if which('restorecon'):
            cmd = 'restorecon ' + path
            exec_command_ex(cmd)
    except subprocess.CalledProcessError as e:
        try:
            os.rmdir(path)
        except (OSError, IOError):
            pass
        raise Exception('Error Mounting disk.', e)

    return path


def which(executable):
    """find the location of an executable"""
    envpath = os.environ.get('PATH') or os.defpath
    PATH = envpath.split(os.pathsep)

    locations = PATH + [
        '/usr/local/bin',
        '/bin',
        '/usr/bin',
        '/usr/local/sbin',
        '/usr/sbin',
        '/sbin',
    ]

    for location in locations:
        executable_path = os.path.join(location, executable)
        if (os.path.isfile(executable_path) and
                os.access(executable_path, os.X_OK)):
            return executable_path


def get_oneliner(base, name):
    path = os.path.join(base, name)
    if os.path.isfile(path):
        with open(path, 'rb') as _file:
            return _bytes2str(_file.readline().rstrip())
    return None


def _bytes2str(string):
    return string.decode('utf-8') if isinstance(string, bytes) else string


def unmount(
        path,
        do_rm=True,
):
    """
    Unmount and removes the given mount point.
    """
    try:
        logger.debug('Unmounting %s', path)
        exec_command_ex('/bin/umount -- ' + path)

    except subprocess.CalledProcessError as e:
        raise Exception('Error unmonting disk.', e)
    if not do_rm:
        return
    os.rmdir(path)


def stmode_is_diskdevice(dmode):
    if stat.S_ISBLK(dmode):
        return True
    else:
        # FreeBSD does not have block devices
        # All disks are character devices
        return False and stat.S_ISCHR(dmode)


def is_partition(dev):
    """
    Check whether a given device path is a partition or a full disk.
    """
    dev = os.path.realpath(dev)
    st = os.lstat(dev)
    if not stmode_is_diskdevice(st.st_mode):
        raise logger.error('not a block device', dev)

    name = get_dev_name(dev)
    if os.path.exists(os.path.join(BLOCKDIR, name)):
        return False

    # make sure it is a partition of something else
    major = os.major(st.st_rdev)
    minor = os.minor(st.st_rdev)
    if os.path.exists('/sys/dev/block/%d:%d/partition' % (major, minor)):
        return True

    raise logger.error('not a disk or partition', dev)


def list_dev(dev, uuid_map, space_map):
    info = {
        'path': dev,
    }

    info['is_partition'] = is_partition(dev)
    if info['is_partition']:
        part_name = get_dev_name(dev)
        ptype = get_partition_type(part_name)
        if ptype == None:
            ptype = 'unknown'
            logger.info("partision {} has no ptype.".format(part_name))
        info['uuid'] = get_partition_uuid(part_name)
    else:
        ptype = 'unknown'
    info['ptype'] = ptype
    if ptype in (PTYPE['osd']):
        info['type'] = 'data'
        list_dev_osd(dev, uuid_map, info)
    elif Ptype.is_regular_space(ptype):
        name = Ptype.space_ptype_to_name(ptype)
        info['type'] = name
        if info.get('uuid') in space_map:
            info[name + '_for'] = space_map[info['uuid']]
    else:
        path = is_mounted(dev)
        fs_type = get_dev_fs(dev)
        if is_swap(dev):
            info['type'] = 'swap'
        else:
            info['type'] = 'other'
        if fs_type:
            info['fs_type'] = fs_type
        if path:
            info['mount'] = path

    return info


def is_swap(dev):
    dev = os.path.realpath(dev)
    with open(PROCDIR + '/swaps', 'rb') as proc_swaps:
        for line in proc_swaps.readlines()[1:]:
            fields = line.split()
            if len(fields) < 3:
                continue
            swaps_dev = fields[0]
            if os.path.isabs(swaps_dev) and os.path.exists(swaps_dev):
                swaps_dev = os.path.realpath(swaps_dev)
                if swaps_dev == dev:
                    return True
    return False


def is_mounted(dev):
    """
    Check if the given device is mounted.
    """
    dev = os.path.realpath(dev)
    with open(PROCDIR + '/mounts', 'rb') as proc_mounts:
        for line in proc_mounts:
            fields = line.split()
            if len(fields) < 3:
                continue
            mounts_dev = fields[0]
            path = fields[1]
            if os.path.isabs(mounts_dev) and os.path.exists(mounts_dev):
                mounts_dev = os.path.realpath(mounts_dev)
                if mounts_dev == dev:
                    return _bytes2str(path)
    return None


def more_osd_info(path, uuid_map, desc):
    desc['ceph_fsid'] = get_oneliner(path, 'ceph_fsid')
    if desc['ceph_fsid']:
        desc['cluster'] = find_cluster_by_uuid(desc['ceph_fsid'])
    desc['whoami'] = get_oneliner(path, 'whoami')
    for name in Space.NAMES:
        uuid = get_oneliner(path, name + '_uuid')
        if uuid:
            desc[name + '_uuid'] = uuid.lower()
            if desc[name + '_uuid'] in uuid_map:
                desc[name + '_dev'] = uuid_map[desc[name + '_uuid']]


def find_cluster_by_uuid(_uuid):
    """
    Find a cluster name by searching /etc/ceph/*.conf for a conf file
    with the right uuid.
    """
    _uuid = _uuid.lower()
    no_fsid = []
    if not os.path.exists(SYSCONFDIR):
        return None
    for conf_file in os.listdir(SYSCONFDIR):
        if not conf_file.endswith('.conf'):
            continue
        cluster = conf_file[:-5]
        try:
            fsid = get_fsid(cluster)
        except Exception as e:
            if 'getting cluster uuid from configuration failed' not in str(e):
                raise e
            no_fsid.append(cluster)
        else:
            if fsid == _uuid:
                return cluster
    # be tolerant of /etc/ceph/ceph.conf without an fsid defined.
    if len(no_fsid) == 1 and no_fsid[0] == 'ceph':
        logger.warning('No fsid defined in ' + SYSCONFDIR +
                       '/ceph.conf; using anyway')
        return 'ceph'
    return None


def list_dev_osd(dev, uuid_map, desc):
    desc['mount'] = is_mounted(dev)
    desc['fs_type'] = get_dev_fs(dev)
    desc['state'] = 'unprepared'
    if desc['mount']:
        desc['state'] = 'active'
        more_osd_info(desc['mount'], uuid_map, desc)
    elif desc['fs_type']:
        try:
            tpath = mount(dev=dev, fstype=desc['fs_type'], options='')
            if tpath:
                try:
                    magic = get_oneliner(tpath, 'magic')
                    if magic is not None:
                        desc['magic'] = magic
                        desc['state'] = 'prepared'
                        more_osd_info(tpath, uuid_map, desc)
                finally:
                    unmount(tpath)
        except subprocess.CalledProcessError as e:
            raise Exception('Error unmonting disk.', e)
            pass


def get_conf_with_default(cluster, variable):
    """
    Get a config value that is known to the C++ code.

    This will fail if called on variables that are not defined in
    common config options.
    """
    try:
        out = exec_command('ceph-osd --no-mon-config --show-config-value=' + variable)
    except subprocess.CalledProcessError as e:
        raise logger.error(
            'getting variable from configuration failed',
            e,
        )
    value = str(out[0]).split('\n', 1)[0]
    return value


def get_fsid(cluster):
    """
    Get the fsid of the cluster.

    :return: The fsid or raises Error.
    """
    fsid = get_conf_with_default(cluster=cluster, variable='fsid')
    # uuids from boost always default to 'the empty uuid'
    if fsid == '00000000-0000-0000-0000-000000000000':
        raise logger.error('getting cluster uuid from configuration failed')
    return fsid.lower()


def list_devices():
    partmap = list_all_partitions()

    uuid_map = {}
    space_map = {}
    for base, parts in sorted(partmap.items()):
        for p in parts:
            dev = get_dev_path(p)
            part_name = get_dev_name(dev)
            part_uuid = get_partition_uuid(part_name)
            if part_uuid:
                uuid_map[part_uuid] = dev
            ptype = get_partition_type(part_name)
            logger.debug("main_list: " + dev +
                         " ptype = " + str(ptype) +
                         " uuid = " + str(part_uuid))
            if ptype == PTYPE['osd']:

                dev_to_mount = dev

                fs_type = get_dev_fs(dev_to_mount)
                if fs_type is not None:

                    try:
                        tpath = mount(dev=dev_to_mount,
                                      fstype=fs_type, options='noatime')
                        try:
                            for name in Space.NAMES:
                                space_uuid = get_oneliner(tpath,
                                                          name + '_uuid')
                                if space_uuid:
                                    space_map[space_uuid.lower()] = dev
                        finally:
                            unmount(tpath)
                    except Exception('Mounting filesystem failed'):
                        pass

    logger.debug("main_list: " + str(partmap) + ", uuid_map = " +
                 str(uuid_map) + ", space_map = " + str(space_map))

    devices = []
    for base, parts in sorted(partmap.items()):
        if parts:
            disk = {'path': get_dev_path(base)}
            partitions = []
            for p in sorted(parts):
                partitions.append(list_dev(get_dev_path(p),
                                           uuid_map,
                                           space_map))
            disk['partitions'] = partitions
            devices.append(disk)
        else:
            device = list_dev(get_dev_path(base), uuid_map, space_map)
            device['path'] = get_dev_path(base)
            devices.append(device)
    logger.debug("list_devices: " + str(devices))
    return devices


def get_partition_name(disk_name, part_num):
    part_name = None
    sys_entry = '/sys/block/' + disk_name
    for f in os.listdir(sys_entry):
        if f.startswith(str(disk_name)) and f.endswith(str(part_num)):
            if not part_name or len(f) < len(part_name):
                part_name = f
    if not part_name:
        if str(disk_name).startswith("sd"):
            part_name = "{}{}".format(disk_name, part_num)
        elif str(disk_name).startswith("nvme"):
            part_name = "{}p{}".format(disk_name, part_num)
    return part_name


def get_device_name(part_name):
    disk_name = None
    for disk_name in os.listdir('/sys/block'):
        if os.path.exists('/sys/block/' + disk_name + '/' + part_name):
            return disk_name
    if str(part_name).startswith("sd"):
        disk_name = ''.join([i for i in part_name if not i.isdigit()])
    elif str(part_name).startswith("nvme"):
        disk_name = str(part_name).split("p")[0]
    return disk_name


def get_partition_num(part_name):
    part_num = ""
    count = 0
    for i in reversed(part_name):
        if i.isdigit():
            count += 1
        else:
            break
    if count == 0:
        return None
    part_num = part_name[-count:]
    return part_num


def get_partition_size(part_name):
    output, err = exec_command(
        "parted /dev/{} unit B print | grep 'Disk /dev/' | tail -n1 | awk '{{print $3}}'".format(part_name))
    partition_size = re.findall(r'-?\d+\.?\d*', output)[0]
    return float(partition_size)


def get_journal_size():
    journal_size = 0
    config = configuration()
    storage_engine = config.get_cluster_info().storage_engine
    cluster_name = config.get_cluster_name()

    if storage_engine == 'filestore':
        journal_size = float(get_conf_with_default(cluster_name, 'osd_journal_size')) * (1024 * 1024)
    elif storage_engine == 'bluestore':
        journal_size = float(get_conf_with_default(cluster_name, 'bluestore_block_db_size'))

    return journal_size


def get_partitions_uuid():
    devs = list_devices()
    partitions_uuid = {}
    for dev in devs:
        if 'partitions' in dev:
            for partition in dev['partitions']:
                if 'uuid' in partition and 'path' in partition:
                    if len(partition['uuid']) > 0 and len(partition['path']) > 0:
                        partitions_uuid.update({partition['uuid']: partition['path']})

    return partitions_uuid
