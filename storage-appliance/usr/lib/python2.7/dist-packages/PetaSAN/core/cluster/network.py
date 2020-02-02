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
import netifaces
from PetaSAN.core.common.ip_utils import *
from PetaSAN.core.entity.network import NetworkInterfaces
from PetaSAN.core.common.cmd import *
import re


class Network:
    def __init__(self):
        pass

    def is_ip_configured(self, _ip):
        ips = self.get_all_configured_ips()
        for ip, eth_name in ips.iteritems():
            ip, mask = str(ip).split("/")
            if ip == _ip:
                return True
        return False

    def get_node_interfaces(self,include_vlans=False):

        """
        :rtype : [NetworkInterfaces]
        """
        eths = list()
        interfaces = netifaces.interfaces()
        for i in interfaces:
            if i == 'lo' or i == 'idrac':
                continue

            if not include_vlans and '.' in i:
                continue

            iface = netifaces.ifaddresses(i).get(netifaces.AF_LINK)
            if iface:
                nf = NetworkInterfaces()
                nf.name = i
                nf.mac = iface[0]['addr']
                eths.append(nf)

        return eths

    def get_node_management_interface(self):

        with open('/etc/network/interfaces', "r") as f:
            lines = f.readlines()
            for line in lines:
                if 'iface' in line:
                    cont = line.split()

                    if '.' in cont[1]:
                        iface = cont[1][:cont[1].index(".")]
                    else:
                        iface = cont[1]

                    interface_bond_name = self.get_interface_bond_name(iface)
                    if interface_bond_name:
                        return interface_bond_name
                    return iface

        raise Exception("There is no management interface set")

    def get_node_management_ip(self):
        # GET IP
        with open('/etc/network/interfaces', "r") as f:
            lines = f.readlines()
            for line in lines:
                if 'address' in line:
                    cont = line.split()
                    ip = cont[1]
                    return ip

        raise Exception("There is no management ip set")

    def get_node_management_base_ip(self):
        management_ip = self.get_node_management_ip()
        management_netmask = self.get_node_management_netmask()
        return get_subnet_base_ip(management_ip, management_netmask)

    def get_node_management_netmask(self):
        # GET Netmask
        with open('/etc/network/interfaces', "r") as f:
            lines = f.readlines()
            for line in lines:
                if 'netmask' in line:
                    cont = line.split()
                    netmask = cont[1]
                    return netmask

        raise Exception("There is no management netmask set")

    def get_node_management_vlan_id(self):
        with open('/etc/network/interfaces', "r") as f:
            lines = f.readlines()
            for line in lines:
                if 'iface' in line:
                    cont = line.split()

                    if '.' in cont[1]:
                        valn_id = cont[1][cont[1].index(".") + 1:]
                    else:
                        valn_id = ''
                    return valn_id

        raise Exception("There is no management interface set")

    def get_def_gateway(self):
        out, err = exec_command('ip r l')
        gateway = out.split('default via')[-1].split()[0]
        r = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        if r.match(gateway) is None:
            return None
        return gateway

    def get_all_configured_ips(self):
        interfaces = netifaces.interfaces()
        ips = dict()
        for i in interfaces:
            if i == 'lo':
                continue

            iface = netifaces.ifaddresses(i).get(netifaces.AF_INET)
            if iface:
                for ip_config in iface:
                    if ip_config['addr']:
                        if not str(ip_config['addr']).startswith("127"):
                            ips[ip_config['addr'] + "/" + ip_config['netmask']] = i

        return ips

    def get_interface_bond_name(self, eth_name):
        config = configuration()
        for b in config.get_cluster_bonds():
            if hasattr(b, "interfaces"):
                if str(b.interfaces).find(eth_name) > -1:
                    return b.name

        return None

    def get_none_bond_interfaces(self):
        eths = []

        config = configuration()
        bonds = config.get_cluster_bonds()
        if len(bonds) == 0:
            return self.get_node_interfaces()
        for eth in self.get_node_interfaces():

            is_exist = False
            for b in bonds:
                if str(b.interfaces).find(eth.name) > -1:
                    is_exist = True
                    break

            if not is_exist:
                eths.append(eth)

        return eths

    def clean_bonding(self):
        if not call_cmd("modprobe bonding"):
            return False
        out, err = exec_command("cat /sys/class/net/bonding_masters")
        if len(err) > 0:
            return False
        out = out.splitlines()
        if len(out) == 0:
            return True

        for l in out[0].split(" "):
            if len(l) == 0:
                continue
            if not call_cmd("echo -{} >  /sys/class/net/bonding_masters".format(l)):
                logger.error("Error clean bond {}.".format(l))
                return False
        return True

    def ping(self, host, wait=2, package=1):

        response = os.system("ping -c {c} -w {w} {h} ".format(c=package, w=wait, h=host))
        if response == 0:
            status = True
        else:
            status = False

        return status
