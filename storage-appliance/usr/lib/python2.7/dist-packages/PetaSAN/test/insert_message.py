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

from itertools import starmap
import os
from PetaSAN.core.config.api import ConfigAPI
is_read = False
old_msgs = dict()
new_msgs = dict()
new_megs_dis = dict()
list = []
message_path =ConfigAPI().get_messages_file_path()
message_path_description = message_path.replace(".txt" , "_description.txt")

def read():
    global is_read
    print "file is reading now."
    if not os.path.exists(message_path) or not os.path.exists(message_path_description):
        raise Exception("Messages files not exists.")

    with open(message_path_description, 'r') as f:
         for line in f.read().splitlines():
             if len(line.strip()) == 0:
                 continue
             line_description = line.split("#")
             k, v = line_description[0].split("=")
             details =line_description[0].split("=")
             list.append(line + '\n')
             old_msgs[str(k).strip()] =str(v).strip()
    is_read= True

def save():


    with open(message_path_description, 'w') as f:
     for key in list:
      print(key)
      f.write(key)
     is_read =False

def add_message(key , value,description):
    if not is_read:
        read()

    if old_msgs.has_key(key) or new_megs_dis.has_key(key):
        raise ValueError("key found >>>>> "+ key)

    else :

        new_megs_dis[key]= value + " # "+description
        line = key + "="+ value+ " # "+description
        list.append(line +'\n')




