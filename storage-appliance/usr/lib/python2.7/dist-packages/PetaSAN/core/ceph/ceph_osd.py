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

from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.ceph.api import CephAPI
import json
from PetaSAN.core.common.cmd import call_cmd, exec_command
from PetaSAN.core.common.enums import OsdStatus
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.ph_disk import DiskInfo


def ceph_osd_tree(node_name):
    ceph_api = CephAPI()
    cluster = None
    node_osds = dict()
    if cluster != -1:

        try:
            cluster = ceph_api.connect()
            out, buf, err = cluster.mon_command(json.dumps({'prefix': 'osd tree', 'format': "json"}), '', timeout=5)
            cluster.shutdown()
            if len(err) > 0:
                return None

            else:
                if len(node_name.split('.')) > 1:
                    node_name = node_name.split('.')[0]

                data = json.loads(buf)

                if data and data.has_key("nodes"):
                    hosts = dict()
                    ceph_osds = dict()
                    for i in data['nodes']:
                        item_type = i.get("type", None)
                        if item_type and item_type == "host":
                            hosts[i.get("name")] = i.get('children')
                        elif item_type and item_type == "osd":
                            ceph_osds[i.get('id')] = i.get('status')

                    if len(hosts) > 0:
                        osds = hosts.get(node_name, None)
                        if osds:
                            for id in osds:
                                if str(ceph_osds.get(id)).lower() == "up":
                                    node_osds[id] = OsdStatus.up
                                else:
                                    node_osds[id] = OsdStatus.down
                            return node_osds
                        else:
                            return None

        except Exception as e:
            cluster.shutdown()
            logger.exception(e.message)
    return None


def ceph_down_osds():
    ceph_api = CephAPI()
    cluster = None
    node_osds = dict()

    if cluster != -1:

        try:
            cluster = ceph_api.connect()
            out, buf, err = cluster.mon_command(json.dumps({'prefix': 'osd tree', 'format': "json"}), '', timeout=5)
            cluster.shutdown()
            if len(err) > 0:
                return None
            else:

                data = json.loads(buf)

                if data and data.has_key("nodes"):
                    hosts = dict()
                    ceph_osds = dict()
                    for i in data['nodes']:
                        item_type = i.get("type", None)
                        if item_type and item_type == "host":
                            hosts[i.get("name")] = i.get('children')
                        elif item_type and item_type == "osd":
                            ceph_osds[i.get('id')] = i.get('status')

                    if len(hosts) > 0:
                        for host, osds in hosts.iteritems():
                            if osds:
                                for id in osds:
                                    if str(ceph_osds.get(id)).lower() != "up":
                                        node_osds[id] = host
            return node_osds

        except Exception as e:
            cluster.shutdown()
            logger.exception(e.message)

    return node_osds


def delete_osd_from_crush_map(osd_id):
    cluster_name = configuration().get_cluster_name()
    logger.info("Start remove osd.{} from crush map".format(osd_id))
    is_executing_without_err = True

    if not call_cmd("ceph --cluster {} osd out osd.{}".format(cluster_name, osd_id)):
        logger.error("Error executing ceph osd out osd.{}".format(osd_id))
        is_executing_without_err = False

    if not call_cmd("ceph --cluster {} osd crush remove osd.{}".format(cluster_name, osd_id)):
        logger.error("Error executing ceph osd crush remove osd.{}".format(osd_id))
        is_executing_without_err = False

    if not call_cmd("ceph --cluster {} auth del osd.{}".format(cluster_name, osd_id)):
        logger.error("Error executing ceph auth del osd.{}".format(osd_id))
        is_executing_without_err = False

    # Try to delete the osd completely from ceph in case the osd is up the next command will not execute
    if not call_cmd("ceph --cluster {} osd rm osd.{}".format(cluster_name, osd_id)):
        logger.warning("The osd still up you need to stop osd service of osd.{}".format(osd_id))

    if is_executing_without_err:
        logger.info("osd.{} is removed from crush map".format(osd_id))
    else:
        logger.warning("osd.{} is removed from crush map".format(osd_id))


def delete_osd(osd_id, disk_name):
    logger.info("Start delete osd.{} from crush map".format(osd_id))
    # cmd = "python {} {}  {}".format(ConfigAPI().get_admin_node_manage_disks_script(), "disk-list -pid", 0)
    # stdout,stderr =exec_command(cmd)
    # data = json.loads(str(stdout))
    # disk_name = None
    # for i in data:
    #     disk_info = DiskInfo()
    #     disk_info.load_json(json.dumps(i))
    #     if str(disk_info.osd_id) == str(osd_id) and disk_info.name !="" :
    #         disk_name = disk_info.name

    # call_cmd(" stop ceph-osd id={}".format(osd_id))

    cluster_name = configuration().get_cluster_name()
    call_cmd("systemctl stop ceph-osd@{}".format(osd_id))
    call_cmd("ceph --cluster {} osd rm osd.{}".format(cluster_name, osd_id))
    call_cmd("umount /var/lib/ceph/osd/{}-{}".format(cluster_name, str(osd_id)))

    logger.info("osd.{} is deleted from crush map".format(osd_id))


def get_osd_id(uuid):
    ceph_api = CephAPI()
    cluster = None
    try:
        cluster = ceph_api.connect()
        out, buf, err = cluster.mon_command(json.dumps({'prefix': 'osd dump', 'format': "json"}), '', timeout=5)
        cluster.shutdown()
        if len(err) > 0:
            return -1

        data = json.loads(buf)
        if data and data.has_key("osds"):
            for osd in data['osds']:
                if osd['uuid'] == uuid:
                    return osd['osd']

    except Exception as e:
        cluster.shutdown()
        logger.exception(e.message)
    return -1


def delete_node_from_crush_map(node_name):
    call_cmd("ceph --cluster {}  osd crush remove {}".format(configuration().get_cluster_name(), node_name))

