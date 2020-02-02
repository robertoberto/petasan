#!/usr/bin/python
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

# import consul
import base64
from time import sleep
from PetaSAN.core.common.log import logger
# import logging
import os
from PetaSAN.core.consul.base import BaseAPI
from PetaSAN.core.config.api import ConfigAPI


class FileSyncManager:
    def __init__(self):
        pass
    root_path = ConfigAPI().get_consul_config_files_path()

    def write_file(self, file_path, value):
        try:
            #logger.info("Trying to Write file" +file_path)

            if os.path.isdir('/'+file_path):
                return
            # Trying to create a new file or open one
            file = open(file_path.replace(self.root_path, ''), 'w')
            file.write(value)
            file.close()
        except Exception as e:
            logger.exception(e.message)
        return

    def commit_file(self, file_path):
        try:
            logger.info("Begin commit_file, key: " + file_path)
            base = BaseAPI()
            logger.info("Begin reading key: " + file_path)

            file = open(file_path, 'r')
            str_value = file.read()
            file.close()
            base.write_value(self.root_path+file_path, base64.b64encode(str_value))
            logger.info("Committed")
            return True
        except Exception as e:
            logger.error("Could not push key ['" + file_path + "'] to consul.")
            logger.exception(e.message)
            return False

    # def sync(self):
    def sync(self, node_key=None):
        #logger.info("Begin sync")

        base = BaseAPI()
        # asynch poll for updates
        current_index = 0#None
        while True:
            try:
                    if node_key is not None:
                        index, data = base.watch(node_key, current_index)
                    else:
                        index, data = base.watch(self.root_path, current_index)
                        print("index", index)
                        print("data", data)
                        print('-------------------------------------')
                    current_index = index
                    if data is not None:
                            # current_index = index
                            print("updated current_index: ",current_index)
                            for data_obj in data:
                                file_path = data_obj['Key'].replace(self.root_path, "")
                                print("file_path")
                                print(file_path)
                                #logger.info("*************************")
                                #logger.info( data_obj['Key'])
                                #logger.info(data_obj['Value'])
                                print("Gonna write file")
                                self.write_file( "/"+data_obj['Key'], base64.b64decode(data_obj['Value']) )
                                print("wrote file")
                    # if index > current_index:
                    #     print("HERE WE ARE")
                    #     if data is not None:
                    #         # current_index = index
                    #         print("updated current_index: ",current_index)
                    #         logger.info(data)
                    #         for data_obj in data:
                    #             file_path = data_obj['Key'].replace(self.root_path, "")
                    #             print("file_path")
                    #             print(file_path)
                    #             logger.info("*************************")
                    #             logger.info( data_obj['Key'])
                    #             logger.info(data_obj['Value'])
                    #             print("Gonna write file")
                    #             self.write_file( "/"+data_obj['Key'], base64.b64decode(data_obj['Value']) )
                    #             print("wrote file")
            except Exception as e:
                print(e.message)
                logger.exception(e.message)
                sleep(2)
        return #my_value
