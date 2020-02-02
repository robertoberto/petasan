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

from PetaSAN.core.entity.path_assignment import PathAssignmentInfo
import random
from PetaSAN.core.path_assignment.base import AssignmentContext
from PetaSAN.core.path_assignment.plugins.average_paths import AveragePathsPlugin

def test(over_nodes_number,under_nodes_numbers,disk_numbers):
    over_nodes = set()
    for i in xrange(1,over_nodes_number+1):
        over_nodes.add("node{}".format(i))

    print over_nodes

    under_nodes = set()
    for i in xrange(over_nodes_number+1,over_nodes_number+under_nodes_numbers+1):
        under_nodes.add("node{}".format(i))
    print  under_nodes

    disks = []
    for i in xrange(1,disk_numbers+1):
        disks.append("disk{}".format(i))
    print disks
    total_paths = (disk_numbers * 8)
    over_paths = int(total_paths*0.9)
    under_paths = total_paths -over_paths

    print "total paths",total_paths,"over paths",over_paths,"blow paths",under_paths



    context =  AssignmentContext()
    context.nodes = (over_nodes|under_nodes)
    # context.nodes.add(set(under_nodes))
    disks_paths = dict()
    for d in disks:
        disks_paths[d] = set()

    add = False
    for i in xrange(1,over_paths+1):

        add = False
        while add != True:
            disk = random.choice(disks)
            if disk == '':
                pass
            ls = disks_paths[disk]
            if len(ls) <= 7:
                node = random.choice(list(over_nodes))
                path = PathAssignmentInfo()

                path.disk_name = disk
                path.disk_id = disk
                path.node = node
                ls.add(path)
                disks_paths[disk] = ls
                add = True
                context.paths.add(path)

    for i in xrange(1,under_paths+1):

        add = False
        while add != True:
            if disk == '':
                pass
            disk = random.choice(disks)
            ls = disks_paths[disk]
            if len(ls) <= 7:
                node = random.choice(list(under_nodes))
                path = PathAssignmentInfo()
                path.disk_name = disk
                path.disk_id = disk
                path.node = node
                ls.add(path)
                disks_paths[disk] = ls
                add = True
                context.paths.add(path)





    paths_count = 0
    for k,v in disks_paths.iteritems():
        # context.paths.union(v)
        paths_count += len(v)

    print  len(context.paths)
    print  paths_count
    plugin = AveragePathsPlugin(context)
    plugin.get_new_assignments()



test(10,3,20)