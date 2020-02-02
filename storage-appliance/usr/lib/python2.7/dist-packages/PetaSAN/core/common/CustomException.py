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

class MetadataException(Exception):
    pass


class DiskListException(Exception):
    DISK_NOT_FOUND = 1
    id = 0

    def __init__(self, id, message):
        super(DiskListException, self).__init__(message)
        self.id = id


class ConfigReadException(Exception):
    pass


class ConfigWriteException(Exception):
    pass


class SSHKeyException(Exception):
    pass


class JoinException(Exception):
    pass


class ReplaceException(Exception):
    pass


class RSAEncryptionException(Exception):
    GENERAL_EXCEPTION = 1
    ENCRYPTION_EXCEPTION = 2
    DECRYPTION_EXCEPTION = 3
    id = 0

    def __init__(self, id, message):
        super(RSAEncryptionException, self).__init__(message)
        self.id = id


class ConsulException(Exception):
    GENERAL_EXCEPTION = 1
    CONNECTION_TIMEOUT = 2
    id = 0

    def __init__(self, id, message):
        super(ConsulException, self).__init__(message)
        self.id = id


class CephException(Exception):
    GENERAL_EXCEPTION = 1
    CONNECTION_TIMEOUT = 2
    id = 0

    def __init__(self, id, message):
        super(CephException, self).__init__(message)
        self.id = id


class ReplicationException(Exception):
    GENERAL_EXCEPTION = 1
    CONNECTION_TIMEOUT = 2
    EXPORT_EXCEPTION = 3
    CONNECTION_REFUSED = 4
    PERMISSION_DENIED = 5
    CEPH_USER_DOES_NOT_EXIST = 6
    DESTINATION_CLUSTER_EXIST = 7
    DESTINATION_CLUSTER_USED_IN_REPLICATION = 8
    DUPLICATE_NAME = 9
    WRONG_CLUSTER_NAME = 10
    SYSTEM_USER_EXIST = 11
    NOT_BACKUP_NODE = 12
    CEPH_USER_EXIST = 13
    id = 0

    def __init__(self, id, message):
        super(ReplicationException, self).__init__(message)
        self.id = id


class PoolException(CephException):
    DUPLICATE_NAME = 100
    PARAMETER_SET = 101
    SIZE_TOO_LARGE = 102
    SIZE_TOO_SMALL = 103
    OSD_PGS_EXCEEDED = 104
    CANNOT_GET_POOL = 105

    def __init__(self, id, message):
        super(PoolException, self).__init__(id, message)


class CrushException(CephException):
    RULE_SAVE = 100
    BUCKET_SAVE = 101
    COMPILE = 102
    DECOMPILE = 103
    DUPLICATE_RULE_NAME = 104
    DUPLICATE_RULE_ID = 105
    RULE_NOT_FOUND = 106
    DEVICE_TYPE_NOT_EXISTS = 107
    DUPLICATE_BUCKET_NAME = 108

    BUCKET_NOT_DEFINED = 150

    def __init__(self, id, message):
        super(CrushException, self).__init__(id, message)


class ECProfileException(CephException):
    DUPLICATE_ECPROFILE_NAME = 100
    ECPROFILE_IN_USE = 200
    WRONG_ECPROFILE_LOCALITY_VALUE = 300
    INVALID_STRIPE_UNIT_ARGUMENT = 400

    def __init__(self, id, message):
        super(ECProfileException, self).__init__(id, message)


class DiskException(CephException):
    JOURNAL_NO_SPACE = 100
    JOURNALS_NO_SPACE = 200
    CACHE_NO_SPACE = 300

    def __init__(self, id, message):
        super(DiskException, self).__init__(id, message)
