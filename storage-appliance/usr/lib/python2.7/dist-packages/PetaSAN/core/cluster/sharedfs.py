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


import subprocess
from time import sleep
import os

from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.entity.cluster import NodeInfo
from PetaSAN.core.ssh.ssh import ssh
import json

from PetaSAN.core.common.log import logger



GFS_BRICK_PATH = '/opt/petasan/config/gfs-brick'
GFS_MOUNT_PATH = '/opt/petasan/config/shared'
GFS_VOL_NAME = 'gfs-vol'
GFS_PING_TIMEOUT = 5
MOUNT_SERVICE= 'petasan-mount-sharedfs'


GFS_CONFIG_DIR = '/var/lib/glusterd'
GFS_PEERS_DIR =  GFS_CONFIG_DIR + '/peers'
GFS_OPERATING_VERSION = '30706'



class SharedFS(object):



    # ================ Management node setup ====================================

    def setup_management_nodes(self):

        current_node=configuration().get_node_info()
        cluster_info = configuration().get_cluster_info()

        if len(cluster_info.management_nodes) != 2 :
            return False

        #ip1 = cluster_info.management_nodes[0]['management_ip']
        #ip2 = cluster_info.management_nodes[1]['management_ip']
        #ip3 =  current_node.management_ip

        #node_info1 = NodeInfo()
        #node_info1.load_json(json.dumps(cluster_info.management_nodes[0]))
        #ip1 = node_info1.backend_1_ip

        ip1 = cluster_info.management_nodes[0]['backend_1_ip']
        ip2 = cluster_info.management_nodes[1]['backend_1_ip']
        ip3 = current_node.backend_1_ip


        # --------------- start service ----------------------------------------

        if subprocess.call('systemctl start glusterd',shell=True) != 0 :
            logger.error("GlusterFS setup_cluster failed to start on local server " + ip3)
            return False
        _ssh = ssh()
        if not _ssh.call_command(ip1,'systemctl start glusterd') :
            logger.error("GlusterFS setup_cluster failed to start on remote server " + ip1)
            return False
        if not _ssh.call_command(ip2,'systemctl start glusterd') :
            logger.error("GlusterFS setup_cluster failed to start on remote server " + ip2)
            return False

        sleep(3)

        # --------------- peering  ----------------------------------------
        if subprocess.call('gluster peer probe ' + ip1,shell=True) != 0 :
            logger.error("GlusterFS setup_cluster failed peer probe with " + ip1)
            return False
        sleep(15)

        if subprocess.call('gluster peer probe ' + ip2,shell=True) != 0 :
            logger.error("GlusterFS setup_cluster failed peer probe with " + ip2)
            return False
        sleep(15)

        """
        # --------------- create volume  ----------------------------------------
        cmd_vol_create = 'gluster vol create ' + GFS_VOL_NAME + ' replica 3'
        cmd_vol_create += ' ' + ip1 +':'+ GFS_BRICK_PATH
        cmd_vol_create += ' ' + ip2 +':'+ GFS_BRICK_PATH
        cmd_vol_create += ' ' + ip3 +':'+ GFS_BRICK_PATH
        
        ret = subprocess.call(cmd_vol_create,shell=True)

        if ret != 0 :
            logger.error("GlusterFS setup_cluster volume create returned: " + str(ret) )
            sleep(3)
        
        sleep(3)

        # --------------- start volume  ----------------------------------------
        if subprocess.call('gluster vol start  ' + GFS_VOL_NAME,shell=True) != 0 :
            logger.error("GlusterFS setup_cluster failed to start volume  " + GFS_VOL_NAME)
            return False

        """

        if not self.vol_create_ex(ip1,ip2,ip3,20,15):
            logger.error("GlusterFS setup_cluster failed to create and start volume  " + GFS_VOL_NAME)
            return False


        # --------------- ping timeout  ----------------------------------------
        if subprocess.call('gluster vol set   ' + GFS_VOL_NAME +
                ' network.ping-timeout ' + str(GFS_PING_TIMEOUT),shell=True) != 0 :
            logger.error("GlusterFS setup_cluster failed to start volume  " + GFS_VOL_NAME)
            return False

        # --------------- disable nfs   ----------------------------------------
        if subprocess.call('gluster vol set   ' + GFS_VOL_NAME +
                ' gfs-vol nfs.disable true ',shell=True) != 0 :
            logger.error("GlusterFS setup_cluster failed to disable nfs on volume  " + GFS_VOL_NAME)
            return False

        #-------------- start mount service ======================================
        # probably not needed since we now call it in start_petasan_services
        subprocess.call('systemctl start ' + MOUNT_SERVICE,shell=True)


        if not _ssh.call_command(ip1,'systemctl start ' + MOUNT_SERVICE)  :
            logger.error("GlusterFS setup_cluster failed to start mount service on remote server " + ip1)
            return False

        if not _ssh.call_command(ip2,'systemctl start ' + MOUNT_SERVICE)  :
            logger.error("GlusterFS setup_cluster failed to start mount service on remote server " + ip2)
            return False

        return True



    def vol_create_ex(self,ip1,ip2,ip3,retries,interval):
        count = 0
        while count < retries:
            if self.vol_create(ip1,ip2,ip3):
                return True
            count += 1
            logger.error("GlusterFS vol_create failed attempt " + str(count) )
            sleep(interval)
        return False


    def vol_create(self,ip1,ip2,ip3):

        cmd_vol_create = 'gluster vol create ' + GFS_VOL_NAME + ' replica 3'
        cmd_vol_create += ' ' + ip1 +':'+ GFS_BRICK_PATH
        cmd_vol_create += ' ' + ip2 +':'+ GFS_BRICK_PATH
        cmd_vol_create += ' ' + ip3 +':'+ GFS_BRICK_PATH
        subprocess.call(cmd_vol_create,shell=True)
        sleep(5)
        if subprocess.call('gluster vol start  ' + GFS_VOL_NAME,shell=True) == 0 :
            return True

        return False


    # ================ Management node replacement ====================================

    def rebuild_management_node(self):

        if subprocess.call('systemctl status glusterd | grep  \"active (running)\"  ' ,shell=True):
            # make sure the server started once to create the config directory
            subprocess.call('systemctl start glusterd',shell=True)
            sleep(5)

        subprocess.call('systemctl stop glusterd',shell=True)
        subprocess.call('killall glusterfsd',shell=True)
        subprocess.call('killall glusterfs',shell=True)

        current_node=configuration().get_node_info()
        other_nodes = configuration().get_remote_nodes_config(current_node.name)

        if len(other_nodes) != 2 :
            return False

        ip1 = other_nodes[0].backend_1_ip
        ip2 = other_nodes[1].backend_1_ip
        ip3 = current_node.backend_1_ip

        _ssh = ssh()
        if not _ssh.copy_dir_from_host(ip1,GFS_PEERS_DIR) :
            logger.error("GlusterFS  Cannot copy peers dir from remote server " + ip1)
            return False
        if not _ssh.copy_dir_from_host(ip2,GFS_PEERS_DIR) :
            logger.error("GlusterFS  Cannot copy peers dir from remote server " + ip2)
            return False

        for fn in os.listdir(GFS_PEERS_DIR):
            if not os.path.isfile(GFS_PEERS_DIR + '/' + fn):
                continue;

            cmd = 'grep \"' + ip3 + '\" ' + GFS_PEERS_DIR + '/' + fn

            if not subprocess.call(cmd ,shell=True):
                """
                f = open(GFS_CONFIG_DIR + '/glusterd.info' , "w")
                f.write('UUID='+fn +'\n')
                f.write('operating-version='+GFS_OPERATING_VERSION)
                f.close()
                """
                cmd2 = 'sed -i \'s/UUID=.*/UUID=' +fn + '/g\' ' + GFS_CONFIG_DIR + '/glusterd.info'
                subprocess.call(cmd2 ,shell=True)
                os.remove(GFS_PEERS_DIR + '/' + fn)

        # start server for peering and getting volume info
        subprocess.call('systemctl start glusterd',shell=True)
        vol_id = self.get_vol_id_ex(5,30)
        if not vol_id:
            logger.error("GlusterFS  Could not get volume id" )
            return False

        # tag the brick with vol id
        cmd = 'setfattr -n trusted.glusterfs.volume-id -v ' + vol_id + ' ' + GFS_BRICK_PATH
        subprocess.call(cmd ,shell=True)


        """
        # per some docs, we should restart gluster here
        subprocess.call('systemctl stop glusterd',shell=True)
        subprocess.call('killall glusterfsd',shell=True)
        subprocess.call('killall glusterfs',shell=True)
        sleep(5)
        subprocess.call('systemctl start glusterd',shell=True)
        sleep(5)

        if not self.vol_heal_ex(3,30):
            logger.error("GlusterFS  Could not start volume heal" )
            return False
        """

        return True



    def vol_heal_ex(self,retries,interval):
        count = 0
        while count < retries:
            if self.vol_heal():
                return True
            count += 1
            logger.error("GlusterFS vol_heal_ex failed attempt " + str(count) )
            sleep(interval)
        return False


    def vol_heal(self):
        cmd = 'gluster volume heal  ' + GFS_VOL_NAME + ' full'
        if subprocess.call(cmd,shell=True) == 0:
            return True
        return False


    def get_vol_id_ex(self,retries,interval):
        count = 0
        while count < retries:
            vol_id = self.get_vol_id()
            if vol_id:
                return vol_id
            count += 1
            logger.error("GlusterFS get_vol_id_ex failed attempt " + str(count) )
            sleep(interval)
        return None


    def get_vol_id(self):
        cmd = 'gluster vol info ' + GFS_VOL_NAME + ' | grep ID | tr -s \' \' | cut -d \' \' -f3'

        vol_id = subprocess.check_output(cmd,shell=True)
        if not vol_id:
            return None
        vol_id = vol_id.rstrip()
        if not vol_id:
            return None
        vol_id = vol_id.replace('-','')
        vol_id = '0x' + vol_id
        return vol_id


    # ================ Storage node setup ====================================

    def setup_storage_node(self):
        subprocess.call('systemctl start ' + MOUNT_SERVICE,shell=True)


    def block_till_mounted(self) :
        cmd_mount_test = 'mount | grep ' + GFS_MOUNT_PATH + ' >/dev/null 2>&1'
        while True :
            if subprocess.call(cmd_mount_test,shell=True) == 0 :
                return True
            sleep(30)
        return False


    def check_mount(self) :

        while True :
            if 2 < len(configuration().get_cluster_info().management_nodes) :
                break
            sleep(30)

        cluster_info = configuration().get_cluster_info()

        #ip1 = cluster_info.management_nodes[0]['management_ip']
        #ip2 = cluster_info.management_nodes[1]['management_ip']

        ip1 = cluster_info.management_nodes[0]['backend_1_ip']
        ip2 = cluster_info.management_nodes[1]['backend_1_ip']

        cmd_mount = 'mount -t glusterfs  -o backupvolfile-server=' + ip2
        cmd_mount += ' ' + ip1 +':'+ GFS_VOL_NAME
        cmd_mount += ' ' + GFS_MOUNT_PATH + ' >/dev/null 2>&1'

        cmd_mount_test = 'mount | grep ' + GFS_MOUNT_PATH + ' >/dev/null 2>&1'

        while True :
            if subprocess.call(cmd_mount_test,shell=True) != 0 :
                logger.info("GlusterFS mount attempt ")
                subprocess.call(cmd_mount,shell=True)
            sleep(30)

        return






