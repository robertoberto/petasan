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
from PetaSAN.core.common.CustomException import MetadataException
from PetaSAN.core.common.log import logger
from PetaSAN.core.common.cmd import exec_command_ex


class Meta_Reader():

    def read_image_metadata(self, io_ctx, meta_object):
        params = {}
        params = self.do_read_image_metadata(io_ctx, meta_object)

        if not params:
            params = self.do_read_image_metadata(io_ctx, meta_object[:-1])

        return params


    # Given io_ctx and object header , Returns xattrs dictionary on this object header
    def do_read_image_metadata(self ,io_ctx , meta_object):
        params = {}
        iterator = io_ctx.get_xattrs(meta_object)

        try:
            while True:
                try:
                    pair = iterator.next()
                    (key, value) = pair

                    if str(value) == "":
                        params[key] = ""
                    else:
                        params[key] = value

                except StopIteration as e:
                    break

                except Exception as e:
                    logger.warning("Cannot parse metadata.")
                    break

            return params

        except Exception as e:
            raise MetadataException("Cannot get metadata.")
