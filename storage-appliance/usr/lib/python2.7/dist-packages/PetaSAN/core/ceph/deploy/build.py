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

from flask import json
import os
import uuid
import time
import sys
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.cluster import NodeInfo
from PetaSAN.core.common.cmd import *
from PetaSAN.core.ssh.ssh import ssh
from PetaSAN.core.entity.status import StatusReport
from PetaSAN.core.ceph.api import CephAPI


def __get_net_size(netmask):
    netmask = netmask.split('.')
    binary_str = ''
    for octet in netmask:
        binary_str += bin(int(octet))[2:].zfill(8)
    return str(len(binary_str.rstrip('0')))


def build_monitors():
    cluster_name = configuration().get_cluster_name()
    ceph_mon_keyring = ConfigAPI().get_ceph_mon_keyring(cluster_name)
    ceph_client_admin_keyring = ConfigAPI().get_ceph_keyring_path(cluster_name)
    status = StatusReport()

    try:
        _fsid = uuid.uuid4()

        content = "[global]\n\
fsid = {fsid}\n\
mon_host = {mon_host}\n\
\n\
public_network = {public_network}\n\
cluster_network = {cluster_network}\n\
\n"

        cluster_config = configuration()
        current_node_info = cluster_config.get_node_info()

        current_node_name = current_node_info.name
        current_cluster_info = cluster_config.get_cluster_info()

        config_api = ConfigAPI()
        mon_hosts_backend_ip = []
        remote_mons_management_ips =[]

        for i in current_cluster_info.management_nodes:
            node_info = NodeInfo()
            node_info.load_json(json.dumps(i))
            mon_hosts_backend_ip.append(node_info.backend_1_ip)
            if current_node_name != node_info.name:
                remote_mons_management_ips.append(node_info.management_ip)

        if not os.path.exists(config_api.get_cluster_ceph_dir_path()):
            os.makedirs(os.path.dirname(config_api.get_cluster_ceph_dir_path()))

        with open(config_api.get_cluster_ceph_dir_path() + "{}.conf".format(cluster_name), 'w', ) as f:
            f.write(content.format(fsid=_fsid,
                                   public_network=str(current_cluster_info.backend_1_base_ip) + "/" + __get_net_size(
                                       str(current_cluster_info.backend_1_mask)),
                                   cluster_network=str(current_cluster_info.backend_2_base_ip) + "/" + __get_net_size(
                                       str(current_cluster_info.backend_2_mask)),
                                   mon_initial=cluster_config.get_node_name(),
                                   mon_host=cluster_config.get_node_info().backend_1_ip+ ','+','.join(mon_hosts_backend_ip)
                                   )+cluster_config.get_ceph_tunings() + "\n"
                    )

        if not call_cmd("ceph-authtool --create-keyring /tmp/{} --gen-key -n mon. --cap mon 'allow *'".format(
                ceph_mon_keyring)) :
            logger.error("ceph-authtool --create-keyring for mon returned error")
            status.success = False

        # elif not call_cmd("".join(["ceph-authtool --create-keyring {}".format(ceph_client_admin_keyring),
        #                    " --gen-key -n client.admin --set-uid=0 --cap mon 'allow *' --cap osd 'allow *' --cap mds 'allow'"])) :
        # Nautilius remove --set-uid=0

        elif not call_cmd("".join(["ceph-authtool --create-keyring {}".format(ceph_client_admin_keyring),
                            " --gen-key -n client.admin --cap mon 'allow *' --cap osd 'allow *' --cap mds 'allow'"])) :
            logger.error("ceph-authtool --create-keyring for admin returned error")
            status.success = False

        elif not call_cmd("ceph-authtool /tmp/{} --import-keyring {}".format(ceph_mon_keyring,ceph_client_admin_keyring)) :
            logger.error("ceph-authtool --import-keyring returned error")
            status.success = False

        elif not call_cmd("monmaptool --create --add {} {} --fsid {} /tmp/monmap".format(cluster_config.get_node_name(),cluster_config.get_node_info().backend_1_ip,_fsid)) :
            logger.error("monmaptool --create --add returned error")
            status.success = False

        if not os.path.exists("/var/lib/ceph/mon/{}-{}".format(cluster_name, current_node_name)):
            os.makedirs("/var/lib/ceph/mon/{}-{}".format(cluster_name, current_node_name))

        if not status.success or not call_cmd("ceph-mon --cluster {} --mkfs -i {} --monmap /tmp/monmap --keyring /tmp/{}".format(cluster_name,current_node_name,ceph_mon_keyring)) :
            logger.error("ceph-mon --mkfs --add returned error")
            status.success = False

        open("/var/lib/ceph/mon/{}-{}/done".format(cluster_name, current_node_name), 'w+').close()
        open("/var/lib/ceph/mon/{}-{}/systemd".format(cluster_name, current_node_name), 'w+').close()

        call_cmd("chown -R ceph:ceph /var/lib/ceph/mon")

        call_cmd("systemctl enable ceph.target ")
        call_cmd("systemctl enable ceph-mon.target ")
        call_cmd("systemctl enable ceph-mon@{} ".format(current_node_name))
        if not status.success or not call_cmd("systemctl start ceph-mon@{}  ".format(current_node_name)):
            status.success = False

        if not status.success:
            status.failed_tasks.append("Create ceph mon on {} returned error.".format(current_node_name))
            return status

        logger.info("First monitor started successfully")

        # create local manager :
        call_cmd('/opt/petasan/scripts/create_mgr.py')

        logger.info("Starting to deploy remote monitors")

        # call_cmd("ceph-create-keys --cluster {} -i {}  ".format(cluster_name,current_node_name))
        # Nautilius copy bootstrap-osd ourselves
        if not os.path.exists("/var/lib/ceph/bootstrap-osd/"):
            os.makedirs("/var/lib/ceph/bootstrap-osd/")
            call_cmd('ceph auth get client.bootstrap-osd > /var/lib/ceph/bootstrap-osd/ceph.keyring')

        for remote_mon in remote_mons_management_ips:
            ssh_obj = ssh()
            if not ssh_obj.copy_file_to_host(remote_mon,"{}".format(ceph_client_admin_keyring)):
                logger.error("Cannot copy {} to {}".format(ceph_client_admin_keyring,remote_mon))
                status.success = False
            elif not ssh_obj.copy_file_to_host(remote_mon,"/etc/ceph/{}.conf".format(cluster_name)):
                logger.error("Cannot copy ceph.conf to {}".format(remote_mon))
                status.success = False
            elif not ssh_obj.call_command(remote_mon," python {} ".format(config_api.get_node_create_mon_script_path())):
                logger.error("Cannot create monitor on remote node {}".format(remote_mon))
                status.success = False

            # Nautilius copy bootstrap-osd ourselves :
            elif not ssh_obj.call_command(remote_mon, 'mkdir -p /var/lib/ceph/bootstrap-osd'):
                logger.error("Cannot create bootstrap-osd dir on remote node {}".format(remote_mon))
                status.success = False
            elif not ssh_obj.copy_file_to_host(remote_mon, '/var/lib/ceph/bootstrap-osd/ceph.keyring'):
                logger.error("Cannot copy bootstrap-osd keyring to {}".format(remote_mon))
                status.success = False

            if not status.success:
                status.failed_tasks.append("core_cluster_deploy_monitor_create_err" + "%" + remote_mon)
                return status
        if not __test_mons():
            status.success = False
            status.failed_tasks.append("core_cluster_deploy_monitors_down_err")
            return status

        # Nautilius enable msgr2 :
        call_cmd('ceph mon enable-msgr2')

    except Exception as ex:
        status.success = False
        logger.exception(ex.message)
        status.failed_tasks.append("core_cluster_deploy_monitor_exception_occurred" + "%" + current_node_name)
        return status

    status.success = True
    return status


def mon_status_check():
    cluster_name = configuration().get_cluster_name()
    out, err = exec_command('ceph --cluster {}  quorum_status '.format(cluster_name))
    for line in err:
        logger.error(line)

    try:
        return json.loads(''.join(out))
    except ValueError:
        return {}


def __test_mons():
    sleeps = [15, 15, 10, 10, 5, 5]
    tries = 5
    mon_in_quorum = []
    mon_members = []

    cluster_conf = configuration()
    current_cluster_info = cluster_conf.get_cluster_info()

    for i in current_cluster_info.management_nodes:
        node_info = NodeInfo()
        node_info.load_json(json.dumps(i))
        mon_members.append(node_info.name)

    for host in mon_members:
        while tries:
            status = mon_status_check()
            has_reached_quorum = host in status.get('quorum_names', '')

            if not has_reached_quorum:
                tries -= 1
                sleep_seconds = sleeps.pop()
                logger.warning('Waiting %s seconds before retrying', sleep_seconds)
                time.sleep(sleep_seconds)
            else:
                mon_in_quorum.append(host)
                break

    if mon_in_quorum == mon_members:
        logger.info("Ceph monitors are ready.")
        return True

    else:
        logger.info("Ceph monitors are not ready.")
        return False


def build_osds():
    cluster_conf = configuration()
    current_node_info = cluster_conf.get_node_info()
    current_node_name = current_node_info.name
    remote_mons_ips = __get_remote_mons_ips(current_node_name)

    logger.info("Start deploying ceph OSDs.")
    status_local = create_osds_local()
    if not status_local.success:
        return status_local

    status_remote = create_osds_remote(remote_mons_ips)
    if not status_remote.success:
        return status_remote

    status_local.failed_tasks.extend(status_remote.failed_tasks)
    return status_local


def create_osds_local():
    config_api = ConfigAPI()
    status = StatusReport()
    out, err = exec_command(" python {} ".format(config_api.get_node_create_osd_script_path()))
    status.load_json(str(out.split("/report/")[1]))

    if os.path.exists(config_api.get_node_pre_config_disks()):
        os.remove(config_api.get_node_pre_config_disks())

    return status


def create_osds_remote(remote_mons_ips_ls):
    config_api = ConfigAPI()
    remote_status = StatusReport()
    for remot_mon in remote_mons_ips_ls:
        ssh_obj = ssh()
        status = StatusReport()

        out, err = ssh_obj.exec_command(remot_mon, " python {} ".format(config_api.get_node_create_osd_script_path()))

        logger.info(" " .join([remot_mon, out]))

        if "/report/" in out:      # To avoid -- IndexError: list index out of range
            status.load_json(str(out.split("/report/")[1]))
        else:
            if err:
                status.load_json("Status Report Error , error : {}".format(str(err)))
            else:
                status.load_json("Connection Error.")

        remote_status.failed_tasks.extend(status.failed_tasks)

        if not status.success:
            logger.error("Cannot create osd for remote node {}".format(remot_mon))
            remote_status.success = False
            return remote_status

    return remote_status


def __get_remote_mons_ips(current_node_name):

    current_cluster_info = configuration().get_cluster_info()
    remote_mons_ips = []
    for i in current_cluster_info.management_nodes:
        node_info = NodeInfo()
        node_info.load_json(json.dumps(i))
        if current_node_name != node_info.name:
            remote_mons_ips.append(node_info.management_ip)
    return remote_mons_ips


def create_rbd_pool():
    cluster_name = configuration().get_cluster_name()
    if not call_cmd("ceph --cluster {} osd pool delete rbd rbd --yes-i-really-really-mean-it ".format(cluster_name)):
        return False

    if not call_cmd("ceph --cluster {} osd pool create rbd 0 ".format(cluster_name)):
        return False

    # Nautilius rbd init seems to hang if pool is not active, use application enable instead
    # call_cmd("rbd pool init rbd")
    call_cmd("ceph osd pool application enable rbd rbd")

    return True


def create_ec_profiles():
    cluster_name = configuration().get_cluster_name()

    if not call_cmd('ceph osd erasure-code-profile set ec-21-profile k=2 m=1 --cluster {}'.format(cluster_name)):
        return False
    if not call_cmd('ceph osd erasure-code-profile set ec-32-profile k=3 m=2 --cluster {}'.format(cluster_name)):
        return False
    if not call_cmd('ceph osd erasure-code-profile set ec-42-profile k=4 m=2 --cluster {}'.format(cluster_name)):
        return False

    if not call_cmd('ceph osd erasure-code-profile set ec-62-profile k=6 m=2 --cluster {}'.format(cluster_name)):
        return False
    if not call_cmd('ceph osd erasure-code-profile set ec-63-profile k=6 m=3 --cluster {}'.format(cluster_name)):
        return False

    return True


def clean_ceph():
    cluster_conf = configuration()
    current_node_info=cluster_conf.get_node_info()
    current_node_name = current_node_info.name
    remote_mons_ips = cluster_conf.get_remote_ips(current_node_name)

    logger.info("Starting clean_ceph")
    clean_ceph_local()
    clean_ceph_remote(remote_mons_ips)


def clean_ceph_local():
    config_api = ConfigAPI()
    call_cmd(" python {} ".format(config_api.get_node_clean_script_path()))


def clean_ceph_remote(ips):
    config_api = ConfigAPI()
    for remot_node in ips:
        ssh_obj = ssh()
        ssh_obj.call_command(remot_node, " python {} ".format(config_api.get_node_clean_script_path()))


def test_active_clean():
    cluster_name = configuration().get_cluster_name()
    sleeps = [10, 15, 20, 25, 30, 40]
    tries = 5

    while tries:
        ceph_api = CephAPI()
        active_pools = ceph_api.get_active_pools()
        if 'rbd' in active_pools:
            logger.info('rbd pool is active')
            break
        tries -= 1
        sleep_seconds = sleeps.pop()
        logger.warning('waiting %s seconds before retrying to check rbd pool status', sleep_seconds)
        time.sleep(sleep_seconds)
  

def test_active_clean_old():
    cluster_name = configuration().get_cluster_name()
    sleeps = [10, 15, 20, 25, 30, 40]
    tries = 5

    while tries:
        status = False
        try:
            out, err = exec_command("ceph --cluster {} -f json pg stat".format(cluster_name))
            ceph_pg_stat = str(out).replace("'", '')
            ceph_pg_stat = json.loads(ceph_pg_stat)
            logger.info("Ceph status is " + ceph_pg_stat['num_pg_by_state'][0]['name'])

            if str(ceph_pg_stat['num_pg_by_state'][0]['name']) == 'active+clean':
                status = True
            else:
                status = False
        except Exception as e:
            logger.error("Get ceph status returned error.\n" + e.message)

        if not status:
            tries -= 1
            sleep_seconds = sleeps.pop()
            logger.warning('waiting %s seconds before retrying to check active+clean status', sleep_seconds)
            time.sleep(sleep_seconds)
        else:
            # Nautilius call pool init when active :
            call_cmd('rbd pool init rbd')
            break


def copy_ceph_config_from_mon():
    cluster_config = configuration()
    cluster_name = cluster_config.get_cluster_name()
    ceph_mon_keyring = ConfigAPI().get_ceph_mon_keyring(cluster_name)
    ceph_client_admin_keyring = ConfigAPI().get_ceph_keyring_path(cluster_name)
    remot_mon_ip = cluster_config.get_remote_ips(cluster_config.get_node_info().name)[0]
    status = StatusReport()
    ssh_obj = ssh()
    config_api = ConfigAPI()
    if not os.path.exists(config_api.get_cluster_ceph_dir_path()):
        os.makedirs(config_api.get_cluster_ceph_dir_path(), exist_ok=True)

    if not os.path.exists("/var/lib/ceph/bootstrap-osd/"):
        os.makedirs("/var/lib/ceph/bootstrap-osd/")

    if not ssh_obj.copy_file_from_host(remot_mon_ip, "{}".format(ceph_client_admin_keyring)):
        logger.error("Cannot copy {} from {}".format(ceph_client_admin_keyring, remot_mon_ip))
        status.success = False
    elif not ssh_obj.copy_file_from_host(remot_mon_ip, "/etc/ceph/{}.conf".format(cluster_name)):
        logger.error("Cannot copy ceph.conf from {}".format(remot_mon_ip))
        status.success = False
    elif not ssh_obj.copy_file_from_host(remot_mon_ip, "/var/lib/ceph/bootstrap-osd/{}.keyring".format(cluster_name)):
        logger.error("Cannot copy ceph.keyring from {}".format(remot_mon_ip))
        status.success = False
    return status


def replace_local_monitor():
    status = copy_ceph_config_from_mon()
    config_api = ConfigAPI()
    if status.success:
        if not call_cmd(" python {} ".format(config_api.get_node_create_mon_script_path())):
            logger.error("Cannot replace monitor")
            status.success = False
            status.failed_tasks.append("core_cluster_replace_monitor_error")
    else:
        status.failed_tasks.append("core_cluster_replace_monitor_copy_error")

    return status


