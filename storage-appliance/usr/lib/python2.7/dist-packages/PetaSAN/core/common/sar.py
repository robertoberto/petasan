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

from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.common.enums import DiskUsage, OsdStatus, SarOutputProperties
from PetaSAN.core.common import disk_util
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.cmd import exec_command, call_cmd
from PetaSAN.core.ceph import ceph_osd, ceph_disk_lib
from PetaSAN.core.entity.benchmark import SarResult, CPU, Iface, Disk
from operator import attrgetter


class Sar(object):
    def __init__(self, include_disk_type=True):
        self.__stat = SarResult()
        self.__header = []
        self.__rows = []
        self.include_disk_type = include_disk_type

    def run(self,duration):
        start_parse = False
        self.__header = []
        self.__rows = []
        self.__stat.node_name = configuration().get_node_name()
        #call_cmd("sync")
        #call_cmd("echo 3| tee /proc/sys/vm/drop_caches &&  sync")
        out, err = exec_command("sar {} 1 -u -P ALL -r -n DEV -d -p".format(duration))

        for line in out.splitlines():

            if not start_parse and line.startswith("Average"):
                start_parse = True
            if start_parse:
                props = line.rsplit()
                if len(props) == 0:
                    self.__process_sar_output_section()

                elif len(self.__header) == 0:
                    props.pop(0)
                    self.__header = props
                else:
                    props.pop(0)
                    self.__rows.append(props)

        self.__process_sar_output_section()
        return self.__stat

    def __process_sar_output_section(self):

        if 'CPU' in self.__header:
            for cpu in self.__rows:
                is_all = False
                if "all" in cpu:
                    is_all = True

                cpu_obj = CPU()
                self.__stat.cpus.append(cpu_obj)

                self.__set_object_properties(cpu_obj, cpu)
                if is_all:
                    continue
                util = round(100.00 - float(cpu_obj.__dict__[SarOutputProperties.cpu_idle]), 2)
                self.__stat.cpu_avg += util
                if util > self.__stat.cpu_max:
                    self.__stat.cpu_max = util
            self.__stat.cpu_avg = round(self.__stat.cpu_avg / (len(self.__rows) - 1), 2)

        elif 'kbmemfree' in self.__header:
            for ram in self.__rows:
                self.__set_object_properties(self.__stat.ram, ram)

        elif 'DEV' in self.__header:
            ph_disk_obj_list = disk_util.get_disk_list()
            ph_disk_list = map(attrgetter('name'), ph_disk_obj_list)
            if self.include_disk_type:
                    local_disks_dict = self.__get_disks()
            for dev in self.__rows:
                if str(dev[0]).startswith("sr") or str(dev[0]).startswith("rbd"):
                    continue
                if str(dev[0]) not in ph_disk_list:
                    continue
                disk_obj = Disk()
                self.__stat.disks.append(disk_obj)
                self.__set_object_properties(disk_obj, dev)
                util = round(float(disk_obj.__dict__[SarOutputProperties.disk_util]), 2)
                self.__stat.disk_avg += util
                if util > self.__stat.disk_max:
                    self.__stat.disk_max = util

                if self.include_disk_type:
                    if dev[0] in local_disks_dict['OSDs']:
                        self.__stat.osd_disks.append(disk_obj)
                        self.__stat.osd_disk_avg += util
                        if util > self.__stat.osd_disk_max:
                            self.__stat.osd_disk_max = util

                    if dev[0] in local_disks_dict['Journals']:
                        self.__stat.journal_disks.append(disk_obj)
                        self.__stat.journal_disk_avg += util
                        if util > self.__stat.journal_disk_max:
                            self.__stat.journal_disk_max = util

            if len(self.__stat.disks) > 0:
                self.__stat.disk_avg = round(self.__stat.disk_avg / (len(self.__stat.disks)), 2)

            if len(self.__stat.osd_disks) > 0:
                self.__stat.osd_disk_avg = round(self.__stat.osd_disk_avg / (len(self.__stat.osd_disks)), 2)

            if len(self.__stat.journal_disks) > 0:
                self.__stat.journal_disk_avg = round(self.__stat.journal_disk_avg / (len(self.__stat.journal_disks)), 2)

        elif 'IFACE' in self.__header:
            self.__stat.iface_avg = 0.0
            node_ifaces = self.__get_ifaces()
            self.__rows.sort(key=self.__get_item)
            for iface in self.__rows:
                if "." in iface[0]:
                    iface[0] = iface[0].replace(".", "-")
                if self.include_disk_type:
                    ignore_this_stat = True
                    for n in node_ifaces:
                        if n in iface[0]:
                            ignore_this_stat = False
                            break
                    if ignore_this_stat:
                        continue
                else:
                    if str(iface[0]).startswith("lo") :
                        continue

                iface_obj = Iface()
                self.__stat.ifaces.append(iface_obj)
                self.__set_object_properties(iface_obj, iface)
                util = round(float(iface_obj.__dict__[SarOutputProperties.iface_ifutil]), 2)
                self.__stat.iface_avg += util
                if util > self.__stat.iface_max:
                    self.__stat.iface_max = util
            if len(self.__stat.ifaces) > 0:
                self.__stat.iface_avg = round(self.__stat.iface_avg / (len(self.__stat.ifaces)), 2)
        self.__header = []
        self.__rows = []
        pass

    def __get_disks(self):
        all_disks_dict = {}
        osd_disks = []
        journal_disks = []
        disk_list = []
        ceph_disk_list = ceph_disk_lib.get_disk_list()
        ph_disk_list = disk_util.get_disk_list()
        osd_dict = ceph_osd.ceph_osd_tree(configuration().get_node_info().name)
        try:
            if ceph_disk_list and len(ceph_disk_list) > 0:
                for disk in ceph_disk_list:
                    for ph_disk in ph_disk_list:
                        if ph_disk.name == disk.name:
                            ph_disk.usage = disk.usage
                            ph_disk.osd_id = disk.osd_id
                            ph_disk.osd_uuid = disk.osd_uuid
                            disk_list.append(ph_disk)
                            break

            for node_disk in disk_list:
                if node_disk.usage == DiskUsage.osd:
                    status = None
                    if osd_dict:
                        status = osd_dict.get(int(node_disk.osd_id), None)
                        if status != None:
                            node_disk.status = status
                            if status == 1:
                                osd_disks.append(node_disk.name)

                elif node_disk.usage == DiskUsage.journal:
                    journal_disks.append(node_disk.name)
            all_disks_dict = {"OSDs": osd_disks, "Journals": journal_disks}
        except Exception as ex:
            logger.error("Cannot get node disks.")
            logger.exception(ex.message)
        return all_disks_dict

    def __get_ifaces(self):
        config = configuration()
        bonds = config.get_cluster_bonds()
        eths = []
        bond_names =[]
        try:
            for bond in bonds:
                eths.extend(bond.interfaces.split(','))
                bond_names.append(bond.name)
            eths.extend(bond_names)
            cluster_info =config.get_cluster_info()
            if not cluster_info.backend_1_eth_name in bond_names and  not cluster_info.backend_1_eth_name in eths:
                eths.append(cluster_info.backend_1_eth_name)
            if not cluster_info.backend_2_eth_name in bond_names and  not cluster_info.backend_2_eth_name in eths:
                eths.append(cluster_info.backend_2_eth_name)
            if not cluster_info.management_eth_name in bond_names and  not cluster_info.management_eth_name in eths:
                eths.append(cluster_info.management_eth_name)
        except Exception as ex:
            logger.error("Cannot get node ifaces.")
            logger.exception(ex.message)
        return eths


        pass
    def __set_object_properties(self, target, source):
        for i in range(0, len(source)):
            target.__dict__[self.__header[i]] = source[i]

    def __get_item(self,item):
        return item[0]
