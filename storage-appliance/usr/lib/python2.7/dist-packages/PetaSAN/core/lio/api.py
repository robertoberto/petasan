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
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.common.enums import ManageDiskStatus, DeleteDiskStatus
from PetaSAN.core.common.log import logger
from PetaSAN.core.entity.disk_info import DiskMeta

from rtslib.tcm import *
from rtslib.target import *


class LioAPI:


    def load_iscsi_mod(self):
        fabric = FabricModule('iscsi')
        if fabric.exists:
            fabric.load()
        elif not fabric.exists:
            logger.error('LIO error cannot load iSCSI fabric module')
            raise Exception('LIO error cannot load iSCSI fabric module')


    def add_target(self, disk_meta, pool):
        """
        :type disk_meta: DiskMeta
        """
        try:
            # fsid = ceph_disk.get_fsid(configuration().get_cluster_name())
            # fsid_split = fsid[: -disk_meta.id]
            # wwn = fsid_split + disk_meta.id

            wwn =  disk_meta.id
            if hasattr(disk_meta,'wwn') and disk_meta.wwn and len(disk_meta.wwn) > 0:
                wwn = disk_meta.wwn
            logger.info('LIO add_target() disk wwn is ' +  wwn)

            rbd_mapped_path = "/".join(["/dev/rbd", pool, ConfigAPI().get_image_name_prefix() + disk_meta.id])
            fabric = FabricModule('iscsi')
            bs = RBDBackstore(0)

            storage_obj = None
            for s in bs.storage_objects:
                if s.name == ConfigAPI().get_image_name_prefix() + disk_meta.id:
                    storage_obj = s
                    break

            if storage_obj is None:
                storage_obj = bs.storage_object(ConfigAPI().get_image_name_prefix() + disk_meta.id, rbd_mapped_path,wwn)
            self.__set_backstore_tunings(storage_obj)
            target = Target(fabric, disk_meta.iqn)

            self.__add__tpgs(disk_meta, target, storage_obj)


        except Exception as e:
            # print "Error open ioctx"
            logger.error("LIO error could not create target for disk %s." % disk_meta.id)
            logger.exception(e.message)
            return ManageDiskStatus.error
        return ManageDiskStatus.done




    def __add__tpgs(self, disk_meta, target, storage):

        """
        :type disk_meta: DiskMeta
        """
        tpg_index = 0
        for path in disk_meta.get_paths():
            tpg_index += 1

            tpg = TPG(target, tpg_index)

            if tpg.luns.gi_running == 0:
                tpg.lun(0, storage, disk_meta.id)

            # "iqn.1991-05.com.microsoft:pc"
            self.__set_tpg_tunings(tpg)
            is_password_set = False
            if disk_meta.acl and str(disk_meta.acl) != "all":
                tpg.set_attribute('generate_node_acls', '0')
                for acl_name in str(disk_meta.acl).split(','):
                    tpg.node_acl(acl_name).mapped_lun(0, 0)
                    if disk_meta.user and disk_meta.password:
                        tpg.node_acl(acl_name).set_auth_attr("userid", disk_meta.user)
                        tpg.node_acl(acl_name).set_auth_attr("password", disk_meta.password)
                        is_password_set = True
            else:
                tpg.set_attribute('generate_node_acls', '1')

            tpg.network_portal(path.ip, 3260)

            if disk_meta.user and disk_meta.password:
                tpg.set_attribute('authentication', '1')
                if not is_password_set:
                    tpg.set_auth_attr("userid", disk_meta.user)
                    tpg.set_auth_attr("password", disk_meta.password)
            else:
                tpg.set_attribute('authentication', '0')

            tpg.set_attribute('demo_mode_write_protect', '0')
            tpg.set_attribute('cache_dynamic_acls', '1')
            tpg.set_parameter('InitialR2T', 'No')
            tpg.set_attribute('tpg_enabled_sendtargets', '0')
            tpg.enable = False



    def delete_target(self, image_name, iqn_name):
        fabric = FabricModule('iscsi')
        try:

            bs = RBDBackstore(0)
            for s in bs.storage_objects:
                if s.name == image_name:
                    storage = s
                    storage.delete()
                    logger.info("LIO deleted backstore image %s " % image_name)
                    break

            target = Target(fabric, iqn_name, "lookup")

            target.delete()
            logger.info("LIO deleted Target %s" % iqn_name)
        except Exception as e:
            logger.error("LIO error deleting Target %s, maybe the iqn is not exists." % iqn_name)
            #logger.exception(e.message)
            return DeleteDiskStatus.error
        return DeleteDiskStatus.done



    def delete_backstore_image(self, image_name):
        fabric = FabricModule('iscsi')
        try:

            bs = RBDBackstore(0)
            for s in bs.storage_objects:
                if s.name == image_name:
                    storage = s
                    storage.delete()
                    logger.info("LIO deleted backstore image %s " % image_name)
                    break
        except Exception as e:
            logger.error("LIO error deleting backstore image  %s." % image_name)
            logger.exception(e.message)
            return DeleteDiskStatus.error
        return DeleteDiskStatus.done

    def get_target_ips(self, iqn_name, path_index=-1):
        ip_list = []
        try:
            fabric = FabricModule('iscsi')

            target = Target(fabric, iqn_name, "lookup")
            for tpgs_obj in target.tpgs:
                if path_index == -1:
                    for portal in tpgs_obj.network_portals:
                        ip_list.append(portal.ip_address)
                elif tpgs_obj.tag == int(path_index):
                    for portal in tpgs_obj.network_portals:
                        ip_list.append(portal.ip_address)
                    break
            return ip_list


        except Exception as e:
            logger.error("LIO error getting target ips for iqn %s." % iqn_name)
            # logger.exception(e.message)

        return ip_list

    def get_backstore_image_names(self):

        bs = RBDBackstore(0)
        backstore = set()
        for s in bs.storage_objects:
            backstore.add(s.name)

        return backstore

    def is_backstore_image_found(self, image_name):
        try:
            bs = RBDBackstore(0)
            for s in bs.storage_objects:
                if s.name == image_name:
                    return True
        except Exception as e:
            logger.error("LIO error cannot check if backstore found for image %s " % image_name)
            logger.exception(e.message)

        return False

    def get_tpg_portal_ips(self, tpg):
        ip = []

        for network_portal_dir in os.listdir("%s/np" % tpg.path):
            if network_portal_dir.startswith('['):
                # # IPv6 portals are [IPv6]:PORT
                # (ip_address, port) = \
                #     os.path.basename(network_portal_dir)[1:].split("]")
                # port = port[1:]
                pass
            else:
                # IPv4 portals are IPv4:PORT
                (ip_address, port) = \
                    os.path.basename(network_portal_dir).split(":")
                # port = int(port)
                ip.append(ip_address)

        return ip

    def enable_path(self, iqn_name, path_index, enable=False):
        try:
            fabric = FabricModule('iscsi')

            target = Target(fabric, iqn_name, "lookup")
            tpg_is_exists = False
            for tpg in target.tpgs:
                if tpg.tag == int(path_index):
                    tpg.set_attribute('tpg_enabled_sendtargets', int(enable))
                    tpg.enable = enable
                    tpg_is_exists = True
                    break

        except Exception as e:
            logger.error(
                "LIO error cannot set path{} to {} for iqn {}.".format(path_index, str(enable), iqn_name))
            raise e
        if tpg_is_exists == False:
            raise Exception(
                "LIO error path{} does not exist for iqn {}.".format(path_index, iqn_name))

    def disable_path(self, iqn_name, path_index):
        try:
            fabric = FabricModule('iscsi')

            target = Target(fabric, iqn_name, "lookup")
            tpg_is_exists = False
            for tpg in target.tpgs:
                if tpg.tag == int(path_index):
                    tpg.set_attribute('tpg_enabled_sendtargets', int(False))
                    tpg.enable = False
                    tpg_is_exists = True
                    break

        except Exception as e:
            logger.error(
                "LIO error cannot  path{} to false for iqn {}.".format(path_index,  iqn_name))
            raise e
        if tpg_is_exists == False:
            raise Exception(
                "LIO error path{} does not exist for iqn {}.".format(path_index, iqn_name))


    def is_path_enabled(self, disk_name, iqn_name, path_index):

        if not self.is_backstore_image_found(disk_name):
            return False
        try:
            fabric = FabricModule('iscsi')

            target = Target(fabric, iqn_name, "lookup")
            for tpg in target.tpgs:
                if tpg.tag == int(path_index):
                    if tpg.enable:
                        return True
                    else:
                        return False
        except Exception as e:
            return False


    def are_all_disk_paths_disabled(self, iqn_name):

        fabric = FabricModule('iscsi')

        target = Target(fabric, iqn_name, "lookup")
        for tpg in target.tpgs:
                if tpg.enable:
                    return False

        return True

    def get_iqns(self):
        fabric = FabricModule('iscsi')
        iqn_list=[]
        for s in fabric.targets:
            iqn_list.append(s.wwn)

        return iqn_list

    def get_iqns_with_tpgs(self):
        iqns = dict()
        try:
            fabric = FabricModule('iscsi')

            for i in fabric.targets:
                iqn = i.wwn
                tpgs = dict()

                target = Target(fabric, iqn, "lookup")
                for tpg in target.tpgs:
                    ip_list = set()
                    for portal in tpg.network_portals:
                        ip_list.add(portal.ip_address)

                    tpgs[str(tpg.tag)]=ip_list

                iqns[iqn]=tpgs
            return iqns

        except Exception as e:
            logger.error("LIO error getting iqns with tpgs.")
            # logger.exception(e.message)

        return iqns


    def get_iqns_with_enabled_tpgs(self):
        iqns = dict()
        try:
            fabric = FabricModule('iscsi')

            for i in fabric.targets:
                iqn = i.wwn
                tpgs = dict()

                target = Target(fabric, iqn, "lookup")
                for tpg in target.tpgs:
                    if not tpg.enable:
                        continue
                    ip_list = set()
                    for portal in tpg.network_portals:
                        ip_list.add(portal.ip_address)

                    tpgs[str(tpg.tag)]=ip_list

                iqns[iqn]=tpgs
            return iqns

        except Exception as e:
            logger.error("LIO error getting iqns with tpgs.")
            # logger.exception(e.message)

        return iqns



    def get_unused_iqns(self):
        iqns = set()
        try:
            fabric = FabricModule('iscsi')

            for i in fabric.targets:
                iqn = i.wwn
                target = Target(fabric, iqn, "lookup")
                is_used = False
                for tpg in target.tpgs:
                    if tpg.enable :
                        is_used = True
                        break
                if not is_used:
                    iqns.add(iqn)
            return iqns

        except Exception as e:
            logger.error("LIO error getting unused iqns.")
            # logger.exception(e.message)

        return iqns


    def __set_backstore_tunings(self,backstore):
        try:
            tunings = configuration().get_lio_backstore_tunings()

            if tunings:
                for k,v in tunings.iteritems():
                    backstore.set_attribute(k,v)
        except Exception as e:
            logger.exception(e.message)
            logger.error("Cannot set backstore tunings. ")

    def __set_tpg_tunings(self,tpg):
        try:
            tuning_param = configuration().get_lio_tpg_tuning_parameters()
            tuning_attr = configuration().get_lio_tpg_tuning_attributes()

            if tuning_param:
                for k,v in tuning_param.iteritems():
                    tpg.set_parameter(k,v)

            if tuning_attr:
                for k,v in tuning_attr.iteritems():
                    tpg.set_attribute(k,v)

        except Exception as e:
            logger.exception(e.message)
            logger.error("Cannot set tpg tunings. ")



