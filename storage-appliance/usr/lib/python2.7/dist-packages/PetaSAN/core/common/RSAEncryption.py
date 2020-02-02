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

import base64
import os
from Crypto.PublicKey import RSA
from PetaSAN.core.common.CustomException import RSAEncryptionException


class RSAEncryption:
    def __init__(self):
        self.prv_key_path = os.path.expanduser('/root/.ssh/id_rsa')
        self.pub_key_path = os.path.expanduser('/root/.ssh/id_rsa.pub')

    def encrypt_public(self, data, local_public_key):
        size = len(data)
        bits = []
        pos = 0
        try:
            chunklen = local_public_key.size() // 8

            while pos < size:
                cipheredText = local_public_key.encrypt(data[pos:pos + chunklen], "")
                bits.append(base64.b64encode(cipheredText[0]))
                pos += chunklen
        except Exception as e:
            raise RSAEncryptionException(RSAEncryptionException.ENCRYPTION_EXCEPTION, 'RSAEncryptionError')

        return bits


    def decrypt_private(self, data, local_private_key):
        plaintext = ""
        try:
            size = len(data)
            for i in range(0, size):
                sub_key = base64.b64decode(data[i])
                plaintext += local_private_key.decrypt(sub_key)
        except Exception as e:
            raise RSAEncryptionException(RSAEncryptionException.DECRYPTION_EXCEPTION, 'RSADecryptionError')

        return plaintext

    def get_key(self, key_path):
        key = ""
        try:
            if os.path.exists(key_path):
                with open(key_path, 'r') as outfile:
                   key_data = outfile.read()
                outfile.close()
                key = RSA.importKey(key_data)
        except Exception as e:
            raise RSAEncryptionException(RSAEncryptionException.GENERAL_EXCEPTION, 'RSAGeneralError')

        return key
