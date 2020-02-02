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

from PetaSAN.core.common.cmd import call_cmd , exec_command_ex
import subprocess
from PetaSAN.core.config.api import ConfigAPI


class NetworkAPI:
    def __init__(self):
        pass

    def add_ip(self, ip, subnet, eth , vlan_id):
        eth_name = eth
        # add vlan_id
        if vlan_id is not None and len(vlan_id) > 0:
            vlan_exist = self.vlan_exists(eth , vlan_id)
            if not vlan_exist:
                create_vlan = self.create_vlan(eth , vlan_id)
                if not create_vlan:
                    return False
            eth_name = eth + "." + vlan_id
        p = subprocess.Popen(["ip", "address", "add", "/".join([ip, subnet]), "dev", eth_name], stdout=subprocess.PIPE)
        output, err = p.communicate()

        return err

    def delete_ip(self, ip, eth, subnet=None):
        eth_name = self.get_eth_name(ip)
        if eth_name is not None and "." in eth_name:
            eth = eth_name
        if subnet:
            p = subprocess.Popen(["ip", "address", "del", "/".join([ip, subnet]), "dev", eth], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            p = subprocess.Popen(["ip", "address", "del", ip, "dev", eth], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.stderr.read()
        if str(out).find("Cannot"):
            return False
        return True

    def update_neighbors_arp(self, ip, eth):
        eth_name = self.get_eth_name(ip)
        if eth_name is not None and "." in eth_name:
            eth = eth_name
        call_cmd("python " +ConfigAPI().get_arping_script_path()+" -ip {} -eth {} &".format(ip,eth))


    def vlan_exists(self , eth , vlan_id):
        cmd = 'ip -d link show {}.{}'.format(eth , vlan_id)
        ret , stdout , stderr = exec_command_ex(cmd)
        if ret != 0:
            return False
        if "does not exist" in stderr:
            return False
        return True

    def create_vlan(self , eth , vlan_id):
        eth_name = eth + "." + vlan_id
        cmd = 'ip link add link {} name {} type vlan id {}'.format(eth , eth_name, vlan_id)
        ret , stdout , stderr = exec_command_ex(cmd)
        if ret != 0:
            return False
        cmd = 'ip link set dev {} up'.format(eth_name)
        ret , stdout , stderr = exec_command_ex(cmd)
        if ret != 0:
            return False
        return True


    def get_eth_name(self, ip):
        cmd = 'ip addr | grep {}'.format(ip)
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            return None
        if stdout and len(stdout) > 0:
            eth_name = stdout.split()[-1]
            return eth_name
        return None
