#! /usr/bin/python
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


from time import sleep
from dialog import Dialog
import socket
import os
from PetaSAN.backend.cluster.deploy import Wizard
import subprocess as sub
from PetaSAN.core.common import interfaces_util
from PetaSAN.core.common.messages import gettext
import json
from PetaSAN.core.common.cmd import exec_command
from PetaSAN.core.config.api import ConfigAPI

HEIGHT = 25
WIDTH = 75
d = Dialog(dialog='dialog', autowidgetsize=True)
d.set_background_title(" PetaSAN 2.4.0")


class Dialog_Customize():
    def get_iface_list(self):
        interface_list = interfaces_util.get_interface_list()
        return interface_list

    def get_cluster_state(self):
        wizard = Wizard()
        cluster_state = wizard.is_cluster_config_complated()
        return cluster_state

    def get_cluster_name(self):
        cluster_name = Wizard().get_cluster_name()
        return cluster_name

    def get_manage_urls(self):
        manage_urls = Wizard().get_management_urls()
        return manage_urls

    def get_node_url(self):
        deploy_url = Wizard().get_node_deploy_url()
        return deploy_url

    def build_interface_elements(self):
        counter = 0
        all_items = []
        for i in self.get_iface_list():
            mac = i.mac
            model = i.model[:54]
            name = i.name
            counter = counter + 1
            item = ("{}    {}".format(mac, model), counter, 1, "{}".format(name), counter, 80, 5, 5)
            all_items.append(item)
        return all_items

    def Equal_Validation(self, interface_list):
        if len(interface_list) > len(set(interface_list)):
            return True

    def get_ifaces(self):
        list = []
        for iface in self.get_iface_list():
            list.append(iface.name)
        return list

    def get_mac_list(self):
        macs = []
        for i in self.get_iface_list():
            macs.append(i.mac)
        return macs

    def create_rule_file(self, dict):
        try:
            with open("/etc/udev/rules.d/70-persistent-net.rules", 'wb+') as f:
                for key in dict:
                    f.write(
                        '\nSUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{}=="{}", ATTR{}=="1", KERNEL=="eth*", NAME="{}" '.format(
                            "{address}", key, "{type}", dict[key]))
                f.close()
            return True
        except:
            return False

    # GET HOSTNAME
    def host_name(self):
        h_name = socket.gethostname()
        return h_name

    # GET DNS
    def get_dns(self):
        with open('/etc/resolv.conf', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'nameserver' in line:
                    cont = line.split()
                    DNS = cont[1]
            return DNS

            # GET INTERFACE

    def get_interface(self):
        with open('/etc/network/interfaces', "r") as f:
            lines = f.readlines()
            for line in lines:
                if 'iface' in line:
                    cont = line.split()
                    iface = cont[1]
            return iface

            # GET IP

    def get_IP(self):
        with open('/etc/network/interfaces', "r") as f:
            lines = f.readlines()
            for line in lines:
                if 'address' in line:
                    cont = line.split()
                    ip = cont[1]
            return ip

            # GET GATEWAY

    def get_gateway(self):
        with open('/etc/network/interfaces', "r") as f:
            lines = f.readlines()
            for line in lines:
                if 'gateway' in line:
                    cont = line.split()
                    gw = cont[1]
            return gw

            ##GET SUBNET MASK

    def get_netmask(self):
        with open('/etc/network/interfaces', "r") as f:
            lines = f.readlines()
            for line in lines:
                if 'netmask' in line:
                    cont = line.split()
                    netmask = cont[1]
            return netmask

    def get_disk_list(self):
        file_path = ConfigAPI().get_manage_node_disk_script()
        cmd = "python {} disk-list -pid 1".format(file_path)
        out, err = exec_command(cmd)
        data = json.loads(out)
        return data

    def build_disk_choices(self):
        disk_list = self.get_disk_list()
        all_disks = []
        counter = 0
        kv_disk = []
        for disk in disk_list:
            if disk['usage'] == 0 or disk['usage'] == 1:
                continue
            name = disk['name']
            size = disk['size']
            type = disk['type']
            vendor = disk['vendor']
            model = disk['model']
            serial = disk['serial']
            counter = counter + 1
            disks = ("{}".format(counter), "{} {} {} {} {} {}".format(name, size, type, vendor, model, serial))
            all_disks.append(disks)
            kv = ("{}".format(counter), "{}".format(name))
            kv_disk.append(kv)
        return kv_disk, all_disks


class Console_Forms():
    def interface_form(self, d):
        cust_dialog = Dialog_Customize()
        kwargs = {"ok_label": "Apply", "no_kill": 1, "no_collapse": 1, "colors": 1}
        code, ifaces = d.form(title="Interface Naming",
                              text="\n{}\n\n MAC Address\t\tModel\t\t\t\t\t\t      Interface".format(gettext("console_interface_naming_form_title_msg")),
                              elements=cust_dialog.build_interface_elements(), **kwargs)
        if code == d.DIALOG_CANCEL or code == d.DIALOG_ESC:
            pass

        for i in ifaces:
            if not i.startswith('eth'):
                d.msgbox("{}".format(gettext("console_interface_naming_empty_item_validation")), title="Error",
                         height=15, width=45)
                if d.DIALOG_OK:
                    return Console_Forms().interface_form(d)
            elif cust_dialog.Equal_Validation(ifaces) == True:
                d.msgbox("{}".format(gettext("console_interface_naming_iterate_fields_validation")), title="Error",
                         height=15, width=45)
                if d.DIALOG_OK:
                    return Console_Forms().interface_form(d)
            elif i not in cust_dialog.get_ifaces():
                d.msgbox("{}".format(gettext("console_interface_naming_ethernet_not_exist")), title="Error", height=15,
                         width=45)
                if d.DIALOG_OK:
                    return Console_Forms().interface_form(d)
        macs = cust_dialog.get_mac_list()
        new_list = dict(zip(macs, ifaces))
        if code == d.DIALOG_OK:
            kwargs = {"extra_button": 1, "extra_label": "Cancel"}
            code = d.msgbox("{}".format(gettext("console_reboot_confirmation_apply_changes")), title="Warning",
                            height=15, width=45, **kwargs)
            if code == d.DIALOG_OK:
                if cust_dialog.create_rule_file(new_list) == True:
                    os.system("reboot")
            if code == d.DIALOG_EXTRA or code == d.DIALOG_ESC:
                return Console_Forms().interface_form(d)

    def disk_menu(self, d):
        kv, disks = Dialog_Customize().build_disk_choices()
        if len(kv) != 0 or len(disks) != 0:
            disk_dic = dict(kv)
            code, tag = d.menu("Test Disk Performance", menu_height=len(kv), height=HEIGHT, width=WIDTH, choices=disks)
            if code == d.DIALOG_CANCEL or code == d.DIALOG_ESC:
                run_console()
            name = disk_dic.get(tag)
            return name
        else:
            code = d.msgbox("{}".format(gettext("console_no_disk_found_msg")), title="{}".format(gettext("console_no_disk_found_msg_title")), height=15, width=45)
            if code == d.DIALOG_OK:
                run_console()

    def threads_menu(self, d):
        code, tag = d.menu("Number of Threads", height=10, width=40, menu_height=3,
                           choices=[("1", ""), ("4", ""), ("8", "")])
        if code == d.DIALOG_CANCEL or code == d.DIALOG_ESC:
            self.run_disk_performance(d)
        if tag == "1":
            threads = 1
        if tag == "4":
            threads = 4
        if tag == "8":
            threads = 8
        return threads

    def performance_output(self, d, name, threads):
        try:
            script_path = ConfigAPI().disk_performance_script()
            cmd = "python {} -disk_name {} -threads_no {} &".format(script_path, name, threads)
            p = sub.Popen([cmd], shell=True, stdout=sub.PIPE)
            code = d.programbox(fd=p.stdout.fileno(), text="Testing disk:{}   threads:{}".format(name, threads),
                                height=HEIGHT, width=WIDTH)
            p.wait()
            if code == d.DIALOG_OK:
                self.run_disk_performance(d)
        except ValueError as e:
            pass

    def warning_box(self, d):
        kwargs = {"extra_button": 1, "extra_label": "Cancel"}
        code = d.msgbox("{}".format(gettext("console_disk_performance_warning_msg")), title="Warning", height=15,
                        width=45, **kwargs)
        if code == d.DIALOG_EXTRA or code == d.DIALOG_CANCEL or code == d.DIALOG_ESC:
            self.run_disk_performance(d)
        if code == d.DIALOG_OK:
            return True

    def run_disk_performance(self, d):
        name = self.disk_menu(d)
        threads = self.threads_menu(d)
        if self.warning_box(d) == True:
            return self.performance_output(d, name, threads)

    def ping_box(self, d):
        kwargs = {"cancel_label": "Back"}
        code, name = d.inputbox("Enter IP to ping", height=HEIGHT, width=WIDTH, **kwargs)
        if code == d.DIALOG_OK:
            try:
                cmd = "ping -c 4  {}  2>&1".format(name)
                p = sub.Popen([cmd], shell=True, stdout=sub.PIPE)
                code = d.programbox(fd=p.stdout.fileno(), text="Pinging\t{}".format(name), height=HEIGHT, width=WIDTH)
                p.wait()
            except ValueError as e:
                pass
        if code == d.DIALOG_CANCEL:
            pass


# RUN CONSOLE
def run_console():
    ##DISABLE CTRL+C
    os.system("stty intr '^_' ")
    # DISABLE CTRL+Z
    os.system("stty susp ^-")
    SHOW_IP = "\nIP Address:\t\t" + Dialog_Customize().get_IP()
    SHOW_SUBMASK = "\nSubnet Mask:\t\t" + Dialog_Customize().get_netmask()
    SHOW_GW="\nGateway:\t\t"+Dialog_Customize().get_gateway()

    interface = Dialog_Customize().get_interface()
    tokens = interface.split('.')
    if 0 < len(tokens) :
        interface = tokens[0]
    SHOW_IFACE = "\nManagement Interface:\t" + interface
    SHOW_VLAN=''
    if 1 < len(tokens) :
        SHOW_VLAN = "\nVLAN:\t\t\t" + tokens[1]

    SHOW_DNS = "\nDNS:\t\t\t" + Dialog_Customize().get_dns()
    SHOW_HNAME = "\nHost Name:\t\t" + Dialog_Customize().host_name()
    NODE_TITLE = "\ZbNode Information:\Zn"
    while (True):
        if Dialog_Customize().get_cluster_state() is False:
            NODE_URL = Dialog_Customize().get_node_url()
            DEPLOY_URL = "\n\Z4\Zu{}\Zn".format(NODE_URL)
            network_config = "\nDeployment Wizard URL:{}\n\n{}\n{}{}{}{}{}{}{}".format(DEPLOY_URL, NODE_TITLE, SHOW_HNAME,
                                                                                     SHOW_IFACE, SHOW_IP, SHOW_SUBMASK,SHOW_VLAN,
                                                                                     SHOW_GW, SHOW_DNS)

            kwargs = {"ok_label": "Options", "no_kill": 1, "no_collapse": 1, "colors": 1}
            code = d.msgbox("" + network_config, title="Node:" + Dialog_Customize().host_name(), height=HEIGHT,
                            width=WIDTH, **kwargs)
            if code == Dialog.OK:
                kwargs = {"ok_label": "Select", "default_button": "cancel", "cancel_label": "Back", "no_kill": 1,
                          "no_collapse": 1}
                code, tag = d.menu("Options", height=HEIGHT, width=WIDTH, menu_height=6,
                                   choices=[("Ping", ""), ("Bash shell", ""), ("Interface Naming", ""),
                                            ("Test Disk Performance", ""), ("Shutdown", ""), ("Reboot", "")], **kwargs)

                if tag == "Bash shell":
                    sub.call("/opt/petasan/scripts/console-shell.sh", shell=True)

                if tag == "Ping":
                    Console_Forms().ping_box(d)

                if tag == "Shutdown":
                    os.system("poweroff")

                if tag == "Reboot":
                    os.system("reboot")
                if tag == "Interface Naming":
                    Console_Forms().interface_form(d)
                if tag == "Test Disk Performance":
                    Console_Forms().run_disk_performance(d)
                sleep(.5)

        if Dialog_Customize().get_cluster_state() is True:
            CLUSTER_NAME = Dialog_Customize().get_cluster_name()
            MANAGEMENT_URL = ('\n'.join(Dialog_Customize().get_manage_urls()))
            mng_cluster = "\nNode is part of PetaSAN cluster {}\nCluster Management URLs:\n\Z4{}\Zu\Zn\n\n{}{}{}{}{}{}{}{}".format(
                CLUSTER_NAME, MANAGEMENT_URL, NODE_TITLE, SHOW_HNAME, SHOW_IFACE, SHOW_IP, SHOW_SUBMASK,SHOW_VLAN,SHOW_GW,
                SHOW_DNS)

            kwargs = {"ok_label": "Options", "no_kill": 1, "no_collapse": 1, "colors": 1}
            code = d.msgbox("" + mng_cluster, height=HEIGHT, width=WIDTH,
                            title="Node:" + Dialog_Customize().host_name(), **kwargs)
            if code == Dialog.OK:
                kwargs = {"ok_label": "Select", "default_button": "cancel", "cancel_label": "Back", "no_kill": 1,
                          "no_collapse": 1, "colors": 1}
                code, tag = d.menu("Options", height=HEIGHT, width=WIDTH, menu_height=5,
                                   choices=[("Ping", ""), ("Interface Naming", ""), ("Test Disk Performance", ""),
                                            ("Shutdown", ""), ("Reboot", "")], **kwargs)

                if tag == "Ping":
                    Console_Forms().ping_box(d)

                if tag == "Shutdown":
                    os.system("poweroff")

                if tag == "Reboot":
                    os.system("reboot")
                if tag == "Interface Naming":
                    Console_Forms().interface_form(d)

                if tag == "Test Disk Performance":
                    Console_Forms().run_disk_performance(d)

                sleep(.5)


run_console()


