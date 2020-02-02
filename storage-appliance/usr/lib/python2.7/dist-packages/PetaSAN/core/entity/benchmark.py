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

from flask import json


class CPU(object):
    def __init__(self):
        pass

    def load_json(self, j):
        self.__dict__ = json.loads(j)


class RAM(object):
    def __init__(self):
        pass

    def load_json(self, j):
        self.__dict__ = json.loads(j)


class Disk(object):
    def __init__(self):
        pass

    def load_json(self, j):
        self.__dict__ = json.loads(j)


class Iface(object):
    def __init__(self):
        pass

    def load_json(self, j):
        self.__dict__ = json.loads(j)


class SarResult(object):
    def __init__(self):
        self.node_name = ""
        self.cpus = []
        self.ram = RAM()

        # all disks
        self.disks = []
        self.disk_max = 0
        self.disk_avg = 0


        # OSDs
        self.osd_disks = []
        self.osd_disk_max = 0
        self.osd_disk_avg = 0

        # journlas
        self.journal_disks = []
        self.journal_disk_max = 0
        self.journal_disk_avg = 0


        self.ifaces = []
        self.cpu_max = 0
        self.cpu_avg = 0

        self.iface_max = 0
        self.iface_avg = 0

        pass

    def load_json(self, j):
        self.__dict__ = json.loads(j)
        pass

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=True, indent=4)
        return j

class RadosResult(object):
    def __init__(self):
        self.node_name = ""
        self.iops= 0
        self.throughput = 0

    def load_json(self, j):
        self.__dict__ = json.loads( j)
        pass

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=True, indent=4)

        return j

class BenchmarkResult(object):
    def __init__(self):
        self.write_iops = 0
        self.read_iops = 0
        self.write_throughput = 0
        self.read_throughput = 0
        self.write_nodes = []
        self.read_nodes = []

    def load_json(self, j):
        self.__dict__ = json.loads(j)
        pass

    def write_json(self):
        j = json.dumps(self, default=lambda o: o.__dict__,
                       sort_keys=True, indent=4)

        return j