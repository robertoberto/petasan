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

import abc

class AssignmentContext(object):
    def __init__(self):
        self.paths = set()
        self.nodes = set()
        self.user_input_paths = None

# get_new_assignments
class BaseAssignmentPlugin(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, context):
        pass

    @abc.abstractmethod
    def is_enable(self):
        return True

    @abc.abstractmethod
    def get_new_assignments(self):
        pass

    @abc.abstractmethod
    def get_plugin_name(self):
        pass

    @abc.abstractmethod
    def get_plugin_id(self):
        pass


