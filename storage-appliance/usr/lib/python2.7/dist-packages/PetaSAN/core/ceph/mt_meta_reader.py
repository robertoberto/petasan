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

from PetaSAN.core.ceph.ceph_connector import CephConnector
from PetaSAN.core.ceph.ceph_authenticator import CephAuthenticator
from PetaSAN.core.ceph.replication.users import Users
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.common.log import logger
from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.config.api import ConfigAPI
import rados, rbd
import threading

key_file = "/etc/ceph/ceph.client.admin.keyring"
config_file = "/etc/ceph/ceph.conf"

meta_key = 'petasan-metada'
thread_count = 5


def readImageMetaData(ioctx, image, pool):
    ret = None

    # Get which ceph user is using this function & get his keyring file path #
    ceph_auth = CephAuthenticator()

    config = configuration()
    cluster_name = config.get_cluster_name()

    try:
        cmd = "rbd info " + pool + "/" + str(image) + " " + ceph_auth.get_authentication_string() + " --cluster " + cluster_name + " | grep rbd_data"
        ret, stdout, stderr = exec_command_ex(cmd)

        if ret != 0:
            if stderr:
                logger.error("Cannot get image meta object from rbd header.")
                return None

        rbd_data = stdout.rstrip().strip()
        dot_indx = rbd_data.rfind(".")

        image_id = rbd_data[(dot_indx+1):]

        rbd_header_object = "rbd_header." + image_id

        try:
            ret = ioctx.get_xattr(rbd_header_object, meta_key)
        except:
            ret = ioctx.get_xattr(rbd_header_object[:-1], meta_key)

    except:
        return None

    return ret


class ReadMetaDataThread(threading.Thread):
    def __init__(self, id, cluster, pool, images):
        threading.Thread.__init__(self)
        self.id = id
        self.cluster = cluster
        self.pool = pool
        self.images = images
        self.image_metada = {}

    def run(self):
        try:
            rbd_inst = rbd.RBD()
            ioctx = self.cluster.open_ioctx(self.pool) 
            for image in self.images:
                meta = readImageMetaData(ioctx, image, self.pool)
                self.image_metada[image] = None
                if meta:
                   # self.image_metada.append(meta)
                    self.image_metada[image] = meta
            ioctx.close()
        except:
            pass
        return

def read_meta(pool) :
    image_metada = {}
    ioctx = None
    cluster = None
    connector = CephConnector()

    try:
        # Get which ceph user is using this function #
        # ========================================== #
        # users = Users()
        # user_name = users.get_current_system_user().strip()
        # if user_name == "root":
        #     user_name = "admin"
        # # Get ceph user's keyring file path #
        # # ================================= #
        # ceph_auth = CephAuthenticator()
        # cluster_name = configuration().get_cluster_name()
        # cluster = rados.Rados(conffile=ConfigAPI().get_ceph_conf_path(cluster_name),conf=dict(keyring=ceph_auth.get_keyring_path()), rados_id=user_name)
        # cluster.connect()

        cluster = connector.connect()
        rbd_inst = rbd.RBD()
        ioctx = cluster.open_ioctx(pool)
        images = rbd_inst.list(ioctx)

        threads = []

        quotient  = len(images) / (thread_count)
        remainder = len(images) % thread_count

        if thread_count <=  len(images):
            images_per_thread = quotient
            for i in range(thread_count):
                thread_images = images[i* images_per_thread  : (i+1) * images_per_thread  ]
                thread = ReadMetaDataThread (i,cluster,pool,thread_images )
                thread.start()
                threads.append(thread)

        remainder_image_metada = {}
        if remainder != 0:
            remainder_images = images[-remainder:]
            for image in remainder_images :
                meta = readImageMetaData(ioctx, image, pool)
                remainder_image_metada[image] = None
                if meta:
                    #remainder_image_metada.append(meta)
                    remainder_image_metada[image] =meta
                    
        for t in threads:
            t.join()

        for t in threads:
            #image_metada.extend( t.image_metada)
            image_metada.update(t.image_metada)

        #image_metada.extend(remainder_image_metada)
        image_metada.update(remainder_image_metada)

        ioctx.close()
    except:
        ioctx.close()
        pass

    cluster.shutdown()

    return image_metada

#image_metada = read_meta()
#for meta in image_metada:
#    print meta
