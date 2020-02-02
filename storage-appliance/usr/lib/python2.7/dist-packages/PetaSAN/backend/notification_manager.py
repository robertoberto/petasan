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

from PetaSAN.core.common.log import logger
from time import sleep
from PetaSAN.core.notification.base import NotifyContext
from threading import Thread

checks_modules = ['PetaSAN.core.notification.plugins.check.cluster',
                  'PetaSAN.core.notification.plugins.check.node',
                  'PetaSAN.core.notification.plugins.check.osd',
                  'PetaSAN.core.notification.plugins.check.smart_health',
                  'PetaSAN.core.notification.plugins.check.replication',
                  'PetaSAN.core.notification.plugins.check.pool',
                  'PetaSAN.core.notification.plugins.check.cluster_status']

notify_modules = ['PetaSAN.core.notification.plugins.notify.message']


class Service:
    def __init__(self, sleep_time=60):
        """

        :type sleep_time: int
        """
        self.__context = NotifyContext()
        self.__sleep_time = sleep_time
        self.__count_of_notify_plugins = -1
        pass

    def start(self):
        self.__process()

    def __process(self):
        while True:
            try:
                self.__do_check()
                self.__do_notify()
            except Exception as ex:
                logger.exception(ex.message)
            sleep(self.__sleep_time)


    def __do_check(self):
        threads_list = []

        for plugin in self.__get_new_plugins_instances(checks_modules):
            if plugin.is_enable:
                plugin.get_plugin_name()
                th = Thread(target=plugin.run)
                th.start()
                threads_list.append(th)

        for t in threads_list:
            t.join()

    def __do_notify(self):
        threads_list = []
        plugins = self.__get_new_plugins_instances(notify_modules)
        if self.__count_of_notify_plugins > -1:
            self.__clean_context_results(self.__count_of_notify_plugins)
        for plugin in plugins:
            if plugin.is_enable:
                plugin.get_plugin_name()
                th = Thread(target=plugin.notify)
                th.start()
                threads_list.append(th)

        for t in threads_list:
            t.join()


        self.__count_of_notify_plugins =len(plugins)


    def __clean_context_results(self, plugins_count):
        remove_results =[]
        for r in  self.__context.results:
            if r.count_of_notify_plugins == plugins_count:
                remove_results.append(r)

        for r in remove_results:
            self.__context.results.remove(r)


    def __get_new_plugins_instances(self, modules):

        plugins = []
        for cls in modules:
            try:
                # import plugins module
                mod_obj = __import__(cls)
                for i in str(cls).split(".")[1:]:
                    mod_obj = getattr(mod_obj, i)
                # Find all plugins in module and create instances
                for mod_prop in dir(mod_obj):
                    # Ignore private
                    if not str(mod_prop).startswith("__"):
                        attr = getattr(mod_obj, mod_prop)
                        attr_str = str(attr)
                        attr_type_str = str(type(attr))
                        # Find plugin from type ABCMeta , plugin class name contains 'plugin' and not contains base
                        if attr_type_str.find("ABCMeta") > -1 and attr_str.find("Base") == -1 and attr_str.find(
                                "Plugin"):
                            instance = attr(self.__context)
                plugins.append(instance)
            except Exception as e:
                logger.error("Error load plugin {}.".format(cls))
        return plugins
