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

from PetaSAN.core.entity.status import EmailStatus
from PetaSAN.core.security.api import UserAPI
from PetaSAN.core.common import email_utils
from PetaSAN.core.common.messages import gettext
from PetaSAN.core.config.api import *
from PetaSAN.core.entity.app_config import AppConfig
from PetaSAN.core.entity.disk_info import Path
from PetaSAN.core.entity.subnet_info import SubnetInfo
from PetaSAN.core.entity.iscsi_subnet import ISCSISubnet

from PetaSAN.core.common.ip_utils import *
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.common.enums import NewIPValidation, PathType
from PetaSAN.core.common.enums import CompressionMode, CompressionAlgorithm

from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.cluster.ntp import NTPConf


class ManageConfig:
    def get_iqn_base(self):
        api = ConfigAPI()
        app_config = api.read_app_config()
        return app_config.iqn_base

    def set_iqn_base(self, iqn_base):
        api = ConfigAPI()
        app_config = api.read_app_config()
        app_config.iqn_base = iqn_base
        api.write_app_config(app_config)

    def set_smtp_config(self, server, port, email, password, security):
        api = ConfigAPI()
        app_config = api.read_app_config()
        app_config.email_notify_smtp_server = server
        app_config.email_notify_smtp_port = port
        app_config.email_notify_smtp_email = email
        app_config.email_notify_smtp_password = password
        app_config.email_notify_smtp_security = security
        api.write_app_config(app_config)

    def get_app_config(self):
        api = ConfigAPI()
        return api.read_app_config()

    def get_iscsi1_subnet(self):
        api = ConfigAPI()
        app_config = api.read_app_config()
        subnet = ISCSISubnet()
        subnet.subnet_mask = app_config.iscsi1_subnet_mask
        subnet.vlan_id = app_config.iscsi1_vlan_id
        subnet.auto_ip_from = app_config.iscsi1_auto_ip_from
        subnet.auto_ip_to = app_config.iscsi1_auto_ip_to
        return subnet

    def set_iscsi1_subnet(self, subnet):
        """
        @type subnet: ISCSISubnet
        """
        api = ConfigAPI()
        app_config = api.read_app_config()
        app_config.iscsi1_subnet_mask = subnet.subnet_mask
        app_config.iscsi1_vlan_id = subnet.vlan_id
        app_config.iscsi1_auto_ip_from = subnet.auto_ip_from
        app_config.iscsi1_auto_ip_to = subnet.auto_ip_to
        api.write_app_config(app_config)

    def get_iscsi2_subnet(self):
        api = ConfigAPI()
        app_config = api.read_app_config()
        subnet = ISCSISubnet()
        subnet.subnet_mask = app_config.iscsi2_subnet_mask
        subnet.vlan_id = app_config.iscsi2_vlan_id
        subnet.auto_ip_from = app_config.iscsi2_auto_ip_from
        subnet.auto_ip_to = app_config.iscsi2_auto_ip_to
        return subnet

    def set_iscsi2_subnet(self, subnet):
        """
        @type subnet: ISCSISubnet
        """
        api = ConfigAPI()
        app_config = api.read_app_config()
        app_config.iscsi2_subnet_mask = subnet.subnet_mask
        app_config.iscsi2_vlan_id = subnet.vlan_id
        app_config.iscsi2_auto_ip_from = subnet.auto_ip_from
        app_config.iscsi2_auto_ip_to = subnet.auto_ip_to
        api.write_app_config(app_config)

    def is_ip_in_iscsi1_subnet(self, ip):
        iscsi1_subnet = self.get_iscsi1_subnet()
        subnet1_base_ip = get_subnet_base_ip(iscsi1_subnet.auto_ip_from, iscsi1_subnet.subnet_mask)
        if is_ip_in_subnet(ip, subnet1_base_ip, iscsi1_subnet.subnet_mask):
            return True
        return False

    def is_ip_in_iscsi2_subnet(self, ip):
        iscsi2_subnet = self.get_iscsi2_subnet()
        subnet2_base_ip = get_subnet_base_ip(iscsi2_subnet.auto_ip_from, iscsi2_subnet.subnet_mask)
        if is_ip_in_subnet(ip, subnet2_base_ip, iscsi2_subnet.subnet_mask):
            return True
        return False

    def validate_new_iscsi1_ip(self, ip):

        if not self.is_ip_in_iscsi1_subnet(ip):
            return NewIPValidation.wrong_subnet

        ips_used = set()
        # get the image metada from ceph
        ceph_api = CephAPI()
        for i in ceph_api.get_disks_meta():
            for p in i.get_paths():
                ips_used.add(p.ip)

        if ip in ips_used:
            return NewIPValidation.used_already

        return NewIPValidation.valid

    def validate_new_iscsi2_ip(self, ip):

        if not self.is_ip_in_iscsi2_subnet(ip):
            return NewIPValidation.wrong_subnet

        ips_used = set()
        # get the image metada from ceph
        ceph_api = CephAPI()
        for i in ceph_api.get_disks_meta():
            for p in i.get_paths():
                ips_used.add(p.ip)

        if ip in ips_used:
            return NewIPValidation.used_already

        return NewIPValidation.valid

    def validate_new_iscsi_ips(self, ips, path_type):

        if path_type == PathType.iscsi_subnet1:
            for ip in ips:
                ret = self.validate_new_iscsi1_ip(ip)
                if ret != NewIPValidation.valid:
                    return ret
            return NewIPValidation.valid

        if path_type == PathType.iscsi_subnet2:
            for ip in ips:
                ret = self.validate_new_iscsi2_ip(ip)
                if ret != NewIPValidation.valid:
                    return ret
            return NewIPValidation.valid

        if path_type == PathType.both:
            if len(ips) != 2:
                return NewIPValidation.invalid_count

            if (self.is_ip_in_iscsi1_subnet(ips[0]) and self.is_ip_in_iscsi2_subnet(ips[1])):

                ip1 = ips[0]
                ip2 = ips[1]

                ret = self.validate_new_iscsi1_ip(ip1)
                if ret != NewIPValidation.valid:
                    return ret

                ret = self.validate_new_iscsi2_ip(ip2)
                if ret != NewIPValidation.valid:
                    return ret

                return NewIPValidation.valid

            if (self.is_ip_in_iscsi1_subnet(ips[1]) and self.is_ip_in_iscsi2_subnet(ips[0])):

                ip1 = ips[1]
                ip2 = ips[0]

                ret = self.validate_new_iscsi2_ip(ip2)
                if ret != NewIPValidation.valid:
                    return ret

                ret = self.validate_new_iscsi1_ip(ip1)
                if ret != NewIPValidation.valid:
                    return ret

                return NewIPValidation.valid

            return NewIPValidation.wrong_subnet

        return NewIPValidation.valid

    def get_path(self, ip):

        path = Path()
        path.ip = ip

        if self.is_ip_in_iscsi1_subnet(ip):
            path.subnet_mask = self.get_iscsi1_subnet().subnet_mask
            path.eth = configuration().get_cluster_info().iscsi_1_eth_name
            path.vlan_id = self.get_iscsi1_subnet().vlan_id
            return path

        if self.is_ip_in_iscsi2_subnet(ip):
            path.subnet_mask = self.get_iscsi2_subnet().subnet_mask
            path.eth = configuration().get_cluster_info().iscsi_2_eth_name
            path.vlan_id = self.get_iscsi2_subnet().vlan_id
            return path

        return None

    def get_new_iscsi_ips(self, path_type, paths_count):

        """
        :rtype paths_list: [Path]
        :type path_type: PathType
        """

        ips_used = set()
        # get the image metada from ceph
        ceph_api = CephAPI()
        for i in ceph_api.get_disks_meta():
            for p in i.get_paths():
                ips_used.add(p.ip)

        iscsi1_subnet = self.get_iscsi1_subnet()
        iscsi2_subnet = self.get_iscsi2_subnet()

        eth1 = configuration().get_cluster_info().iscsi_1_eth_name
        eth2 = configuration().get_cluster_info().iscsi_2_eth_name

        path_list = []

        if path_type == PathType.iscsi_subnet1:
            gen1 = IPAddressGenerator(iscsi1_subnet.auto_ip_from, iscsi1_subnet.auto_ip_to)
            while gen1.has_next():
                ip1 = gen1.get_next()
                if (not ip1 in ips_used):
                    path_list.append(self.get_path(ip1))
                    if len(path_list) == paths_count:
                        return path_list
                else:
                    path_list = []

            # return None
            return []

        if path_type == PathType.iscsi_subnet2:
            gen2 = IPAddressGenerator(iscsi2_subnet.auto_ip_from, iscsi2_subnet.auto_ip_to)
            while gen2.has_next():
                ip2 = gen2.get_next()
                if (not ip2 in ips_used):
                    path_list.append(self.get_path(ip2))
                    if len(path_list) == paths_count:
                        return path_list
                else:
                    path_list = []

            # return None
            return []

        if path_type == PathType.both:

            gen1 = IPAddressGenerator(iscsi1_subnet.auto_ip_from, iscsi1_subnet.auto_ip_to)
            gen2 = IPAddressGenerator(iscsi2_subnet.auto_ip_from, iscsi2_subnet.auto_ip_to)

            while gen1.has_next() and gen2.has_next():
                # we increment both ranges together so they remain related
                ip1 = gen1.get_next()
                ip2 = gen2.get_next()
                if ((not ip1 in ips_used) and (not ip2 in ips_used)):

                    path_list.append(self.get_path(ip1))
                    if len(path_list) == paths_count:
                        return path_list

                    path_list.append(self.get_path(ip2))
                    if len(path_list) == paths_count:
                        return path_list

                else:
                    path_list = []

            # return None
            return []


        # return None
        return []

    def get_ntp_server(self):
        ntp = NTPConf()
        return ntp.get_ntp_server_remote()

    def save_ntp_server(self, ntp_server):
        ntp = NTPConf()
        return ntp.set_ntp_server_remote(ntp_server)

    def get_replicas(self, pool="rbd"):
        return CephAPI().get_replicas(pool)

    def set_replicas(self, size, pool="rbd"):
        return CephAPI().set_replicas(size, pool)

    def test_email(self,sender_email,server,port,password,security,logged_in_user_name):
        user_api = UserAPI()
        status = EmailStatus()
        user = user_api.get_user(logged_in_user_name)
        if not user.notfiy:
            status.success = False
            status.err_msg = gettext("core_email_test_user_not_set_receive_notify")
            return status
        elif len(user.email.strip()) == 0:
            status.success = False
            status.err_msg = gettext("core_email_test_user_not_set_receive_email")
            return status

        msg = email_utils.create_msg(sender_email, user.email, gettext("core_email_test_subject"), gettext("core_email_test_body"))
        status = email_utils.send_email(server, port, msg ,password, security)
        return status

    def get_compression_mode(self, pool='rbd'):
        api = CephAPI()
        mode = api.get_compression_mode(pool)
        if mode is None or mode is '' or "none" in mode:
            return CompressionMode.none
        if 'force' in mode:
            return CompressionMode.force
        raise Exception("Compression mode is not valid")

    def get_compression_algorithm(self, pool="rbd"):
        api = CephAPI()
        algorithm = api.get_compression_algorithm(pool)

        if algorithm is None or algorithm is '' or "none" in algorithm:
            return CompressionAlgorithm.none
        if 'zlib' in algorithm:
            return CompressionAlgorithm.zlib
        if 'snappy' in algorithm:
            return CompressionAlgorithm.snappy
        if 'zstd' in algorithm:
            return CompressionAlgorithm.zstd
        if 'lz4' in algorithm:
            return CompressionAlgorithm.lz4
        raise Exception("Compression algorithm is not valid")

    def set_compression_mode(self, mode, pool="rbd"):
        api = CephAPI()
        if mode == CompressionMode.none:
            mode_str = 'none'
        elif mode == CompressionMode.force:
            mode_str = 'force'
        return api.set_compression_mode(mode_str, pool)

    def set_compression_algorithm(self, algorithm, pool="rbd"):
        api = CephAPI()
        if algorithm == CompressionAlgorithm.none:
            algorithm_str = 'none'
        elif algorithm == CompressionAlgorithm.zlib:
            algorithm_str = 'zlib'
        elif algorithm == CompressionAlgorithm.snappy:
            algorithm_str = 'snappy'
        elif algorithm == CompressionAlgorithm.zstd:
            algorithm_str = 'zstd'
        elif algorithm == CompressionAlgorithm.lz4:
            algorithm_str = 'lz4'
        return api.set_compression_algorithm(algorithm_str, pool)