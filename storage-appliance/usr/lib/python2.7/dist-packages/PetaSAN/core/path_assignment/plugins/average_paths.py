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

from PetaSAN.core.common.enums import ReassignPathStatus
from PetaSAN.core.common import log
from PetaSAN.core.entity.path_assignment import PathAssignmentInfo
from collections import Counter
from PetaSAN.core.path_assignment.base import BaseAssignmentPlugin, AssignmentContext


class AveragePathsPlugin(BaseAssignmentPlugin):

    def __init__(self, context):
        self.__disk_paths = dict()
        self.__over_average_nodes = dict()
        self.__below_average_nodes = dict()
        self.__context = AssignmentContext()
        self.__average = 0
        self.__context = context


    def get_plugin_id(self):
        return 1

    def __process(self):
        # Step 1: Calc average
        self.__average = len(self.__context.paths) / len(self.__context.nodes)
        if len(self.__context.paths) % len(self.__context.nodes) >0:
            self.__average +=1


        # Step 2: Distribute paths for each node
        for node in self.__context.nodes:
            self.__disk_paths[node] = set()

        for path in self.__context.paths:
            paths = self.__disk_paths.get(path.node)
            paths.add(path)
            self.__disk_paths[path.node] = paths

        # Step 3: divided nodes by below and average paths
        for node, paths in self.__disk_paths.iteritems():
            if len(paths) > self.__average:
                self.__over_average_nodes[node] = paths
                log.logger.debug("Node {} is over average ,paths count {}  ".format(node, len(paths)))
            elif len(paths) < self.__average:
                self.__below_average_nodes[node] = paths

                log.logger.debug("Node {} is below average ,paths count {}  ".format(node, len(paths)))


    def get_new_assignments(self):
        self.__process()
        over_average_paths = set()
        if len(self.__below_average_nodes)== 0:
            return over_average_paths
        if self.__context.user_input_paths is not None:
            over_average_paths = self.__context.user_input_paths
        else:
            # Step 1: Get over average paths from nodes that exceed average
            for node, disk_paths in self.__over_average_nodes.iteritems():
                log.logger.debug("Sort disks by paths count for {}".format(node))
                # The following will help to sort disks on node by disk paths count then ...
                # .. continua pop path until the node paths count equals average
                sort_disks = SortNodeDisks(self.__average, disk_paths)
                path = PathAssignmentInfo()
                while path is not None:
                    log.logger.debug("Get a path from the highest disk paths count from top node on paths count.")
                    path = sort_disks.pop()
                    if path is not None:
                        over_average_paths.add(path)
            log.logger.debug("Total of reassignment paths is {}.".format(len(over_average_paths)))
            self.__over_average_nodes = None

        # Step 2: Find the recommend node for each over average path
        sort_recommend_node = SortRecommendNode(self.__average, over_average_paths, self.__below_average_nodes)
        path = PathAssignmentInfo()
        over_average_paths = set()
        while path is not None:
            path = sort_recommend_node.pop()
            if path is not None:
                over_average_paths.add(path)
        return over_average_paths

    def is_enable(self):
        return True

    def get_plugin_name(self):
        return 'AveragePathsPlugin'


class SortNodeDisks(object):
    def __init__(self, average, node_paths):
        self.__paths = node_paths

        # __sort_disks_by_count contains disk as key and paths count as a value
        # This help to sort disks by count of paths before and after add or remove path
        self.__sort_disks_by_count = Counter()

        # __disk_paths dictionary contains disk as key and paths as a set in the value
        # This help to find a disk path to remove or add it under its disk.
        self.__disk_paths = dict()

        self.__max_remove_paths = len(node_paths) - average

        # Count paths for each disk and set relation between disk and its path
        for path in self.__paths:

            self.__sort_disks_by_count[path.disk_id] += 1
            disk_paths = self.__disk_paths.get(path.disk_id)
            if disk_paths is None:
                disk_paths = set()
            disk_paths.add(path)
            self.__disk_paths[path.disk_id] = disk_paths

        log.logger.debug(self.__sort_disks_by_count)

    def pop(self):
        path = None

        if self.__max_remove_paths == 0:
            return path
        # Get the top disk has paths
        disk_paths = self.__sort_disks_by_count.most_common(1)
        log.logger.debug(disk_paths)

        if disk_paths:
            disk_id, paths_count = disk_paths[0]
            if paths_count > 0:
                # Decrease the number of the paths that we should remove from this node by 1.
                self.__max_remove_paths -= 1
                # Find the disk and get paths set and get path.
                paths = self.__disk_paths.get(disk_id)
                path = paths.pop()
                self.__sort_disks_by_count[disk_id] -= 1
                log.logger.debug(self.__sort_disks_by_count)
        log.logger.debug(
            "Over average path ,node is {},disk is {} and ip is{}".format(path.node, path.disk_id, path.ip))
        return path


class SortRecommendNode(object):
    def __init__(self, average, over_average_paths, below_average_nodes):
        log.logger.debug("Sort Recommend Node")
        self.__over_average_paths = over_average_paths

        # __node_paths_per_disk is a dictionary contains disk as key and value is counter object ...
        # contains node as key and value is count of paths for a disk
        self.__node_paths_count_per_disk = dict()

        # __paths_per_node is a dictionary contains node as key and value total count of paths per node
        self.__paths_per_node = Counter()
        self.__average = average
        self.__nodes = below_average_nodes.keys()

        # Prepare over average disk
        for path in over_average_paths:
            node_paths_counter = Counter()
            self.__node_paths_count_per_disk[path.disk_id] = node_paths_counter
            # for node in self.__nodes:
            #     node_paths_counter[node] = 0

        # Distribute below_average_nodes ,
        # count paths per node and count paths for each node to a certain disk
        for node, paths in below_average_nodes.iteritems():
            self.__paths_per_node[node] = len(paths)
            for path in paths:
                disk_paths_per_node = self.__node_paths_count_per_disk.get(path.disk_id)
                if disk_paths_per_node is not None:
                    disk_paths_per_node[node] += 1

        log.logger.debug("==================================================")
        log.logger.debug("      {}".format(self.__node_paths_count_per_disk))
        log.logger.debug("      {}".format(self.__paths_per_node))
        log.logger.debug("==================================================")

    def pop(self):
        # The following will help to sort below average nodes depend on ..
        path = None
        if self.__average == 0 or len(self.__over_average_paths) == 0:
            return path
        path = self.__over_average_paths.pop()
        if path:
            # Get counter object that contains node as a key and paths count for a select disk
            disk_paths_counter_per_node = self.__node_paths_count_per_disk.get(path.disk_id)
            recommended_nodes = set()
            if disk_paths_counter_per_node is not None:
                # Get a list of nodes sorted by paths count descending order
                disk_paths_per_node_ls = disk_paths_counter_per_node.most_common()
                nodes_count = len(disk_paths_per_node_ls) - 1
                min_paths_count = None
                # Get the set of nodes that has the same lowest count of paths.
                while -1 != nodes_count:
                    # Start from the lowest one.
                    node, paths_count = disk_paths_per_node_ls[nodes_count]
                    if (min_paths_count is not None and paths_count <= min_paths_count) or min_paths_count is None:
                        min_paths_count = paths_count
                        nodes_count -= 1
                        recommended_nodes.add(node)
                    else:
                        break

                log.logger.debug(
                    "List of the smallest nodes {} on paths count for disk {}.".format(recommended_nodes, path.disk_id))
            recommend_node = None
            # If we have more than node share the same count of the paths for a disk ...
            # ..we will find the lowest node in the total count of paths
            # Then we check if there is any node did not has the path so it will override the recommended node

            lowest_paths_count = None
            for node in recommended_nodes:
                paths_count = self.__paths_per_node.get(node)
                if paths_count < self.__average and (
                                lowest_paths_count is None or paths_count < lowest_paths_count):
                    lowest_paths_count = paths_count
                    recommend_node = node
            if disk_paths_counter_per_node is not None and len(disk_paths_counter_per_node) < len(self.__paths_per_node):
                most_common = self.__paths_per_node.most_common()
                most_common_count = len(most_common) - 1
                while -1 != most_common_count:
                    node, count = most_common[most_common_count]
                    most_common_count -= 1
                    if node not in recommended_nodes and count < self.__average:
                        log.logger.debug(
                            "Override recommended node {} by node {} does not has this path.".format(recommend_node,
                                                                                                     node))
                        recommend_node = node
                        break
                    elif count >= self.__average:
                        break
            last_node, last_node_paths_count = self.__paths_per_node.most_common()[len(self.__paths_per_node) - 1]
           # Increase the number of the paths
            if not recommend_node:
                recommend_node = last_node
            if recommend_node == last_node:
                paths_count = self.__paths_per_node.get(recommend_node)
                # if the lowest node in count of paths is over average that mean all nodes now over average.
                if paths_count >= self.__average:
                    log.logger.info("All nodes now are over average.")
                    return None
            self.__paths_per_node[recommend_node] += 1
            disk_paths_counter_per_node[recommend_node] += 1
            if self.__paths_per_node.get(path.node):
                self.__paths_per_node[path.node] -=1
            if disk_paths_counter_per_node.get(path.node):
                disk_paths_counter_per_node[path.node] -= 1


            path.target_node = recommend_node
            path.status = ReassignPathStatus.pending
            log.logger.debug(
                ">>>Target node {} for disk path {} from node {}.".format(recommend_node, path.disk_id, path.node))
            log.logger.debug("      {}".format(self.__node_paths_count_per_disk))
            log.logger.debug("      {}".format(self.__paths_per_node))

        return path
