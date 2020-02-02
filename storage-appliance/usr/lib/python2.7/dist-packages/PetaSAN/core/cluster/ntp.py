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
import time


from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.ssh.ssh import ssh

NTP_CONF_PATH = '/etc/ntp.conf'
#NTP_STOP_CMD = '/etc/init.d/ntp stop'
#NTP_START_CMD = '/etc/init.d/ntp start'

NTP_STOP_CMD = 'systemctl stop ntp'
NTP_START_CMD = 'systemctl start ntp'


GET_NTP_SERVER_REMOTE_SCRIPT = '/opt/petasan/scripts/get_ntp_server.py'
SET_NTP_SERVER_REMOTE_SCRIPT = '/opt/petasan/scripts/set_ntp_server.py'


LOCAL_STRATUM_BASE = 7
LOCAL_STRATUM_HOP = 2



class NTPConf(object):

    def setup_ntp_local(self):

        self.force_ntp_sync()

        current_node=configuration().get_node_info()
        cluster_info = configuration().get_cluster_info()

        server_ips = []
        for node in cluster_info.management_nodes :
            if current_node.management_ip == node['management_ip'] :
                break
            server_ips.append(node['management_ip'] )

        stratum_local = LOCAL_STRATUM_BASE + len(server_ips) * LOCAL_STRATUM_HOP
        self.build_conf_file(server_ips,False,stratum_local)

        self.stop_ntp()
        time.sleep(2)
        self.start_ntp()
        return


    def get_ntp_server_remote(self) :

        cluster_info = configuration().get_cluster_info()
        if len(cluster_info.management_nodes) == 0 :
            return None
        node = cluster_info.management_nodes[0]
        ip = node['management_ip']

        _ssh = ssh()
        remote_ret =  _ssh.get_remote_object(ip,GET_NTP_SERVER_REMOTE_SCRIPT)
        if remote_ret is None :
            return None

        if remote_ret['success'] is False :
            return None

        return remote_ret['ntp_server']


    def set_ntp_server_remote(self,server) :

        cluster_info = configuration().get_cluster_info()
        if len(cluster_info.management_nodes) == 0 :
            return None
        node = cluster_info.management_nodes[0]
        ip = node['management_ip']

        _ssh = ssh()
        ret =  _ssh.call_command(ip,SET_NTP_SERVER_REMOTE_SCRIPT + ' ' + server)
        return ret


    def get_ntp_server_local(self) :
        ret = ''
        with open(NTP_CONF_PATH,'r') as f:
            #lines = f.readlines()
            lines = f.read().splitlines()
            for line in lines :
                #line = line.replace('\n','')
                if  'server' in line:
                    tokens = line.split()
                    if( tokens[1] != '127.127.1.0') :
                        ret = tokens[1]
                        break
        return ret



    def set_ntp_server_local(self,server) :
        server_ips = [server]
        self.build_conf_file(server_ips,True,LOCAL_STRATUM_BASE)
        self.stop_ntp()
        self.start_ntp()

        return


    def force_ntp_sync(self):

        cluster_info = configuration().get_cluster_info()
        server_ips = []
        for node in cluster_info.management_nodes :
            server_ips.append(node['management_ip'] )

        if len(server_ips) == 0 :
            return

        current_node=configuration().get_node_info()
        if current_node.management_ip == server_ips[0] :
            return

        self.stop_ntp()
        time.sleep(2)
        cmd = 'ntpdate  ' + server_ips[0]
        subprocess.call(cmd,shell=True)
        self.start_ntp()

        self.sync_hw_clock()

        return


    def sync_hw_clock(self):
        cmd = 'hwclock --systohc --utc  '
        subprocess.call(cmd,shell=True)

        return

    def build_conf_file(self,server_ips,internet,stratum_local) :
        conf_string  = 'driftfile /var/lib/ntp/ntp.drift\n'
        conf_string += '\n'

        for server_ip in server_ips :
            conf_string += 'server  ' +  server_ip
            if not internet:
                conf_string += ' burst '
            conf_string += ' iburst  \n'

        conf_string += '\n'
        conf_string += 'server  127.127.1.0 \n'
        conf_string += 'fudge   127.127.1.0 stratum {} \n'.format(stratum_local)

        """
        node_info = configuration().get_node_info()
        node_ip = node_info.management_ip
        conf_string += '\n'
        conf_string += 'interface ignore wildcard \n'
        conf_string += 'interface listen {}'.format(node_ip)
        """

        conf_file = open(NTP_CONF_PATH,'w')
        conf_file.write(conf_string)
        conf_file.close()

        return



    def stop_ntp(self) :
        subprocess.call(NTP_STOP_CMD,shell=True)
        return



    def start_ntp(self) :
        subprocess.call(NTP_START_CMD,shell=True)
        return


