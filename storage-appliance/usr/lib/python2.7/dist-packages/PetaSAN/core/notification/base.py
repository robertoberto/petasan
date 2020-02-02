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


class NotifyContext(object):
    def __init__(self):
        self.results = []
        self.state = {}


class Result(object):
    def __init__(self):
        self.message = ""
        self.plugin_name = ""
        self.title = ""
        self.count_of_notify_plugins = 0


class CheckBasePlugin(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, context):
        pass

    @abc.abstractmethod
    def is_enable(self):
        return True

    @abc.abstractmethod
    def run(self):
        pass

    @abc.abstractmethod
    def get_plugin_name(self):
        pass


class NotifyBasePlugin(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, context):
        pass

    @abc.abstractmethod
    def is_enable(self):
        return True

    @abc.abstractmethod
    def notify(self):
        pass

    @abc.abstractmethod
    def _get_supported_plugins(self):
        return []

    @abc.abstractmethod
    def _get_followers(self):
        return []

    @abc.abstractmethod
    def get_plugin_name(self):
        pass
