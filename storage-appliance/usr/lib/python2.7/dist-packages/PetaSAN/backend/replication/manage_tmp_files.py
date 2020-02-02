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

from PetaSAN.core.common.cmd import exec_command_ex
from PetaSAN.core.common.log import logger


class ManageTmpFile:
    def __init__(self):
        pass

    # ##################################################################################################################
    def create_tmp_file(self,sshkey_path , decrypted_key):
        f = open(sshkey_path, "w+")
        f.write(decrypted_key)
        f.close()

    # ##################################################################################################################
    def delete_tmp_file(self, file_name):
        cmd = "rm -f {}".format(file_name)
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            logger.error('Manage Tmp File | Error , delete tmp file : ' + cmd)
        return True