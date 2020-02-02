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

from PetaSAN.core.config.api import ConfigAPI
import os
is_read = False
old_msgs = dict()
list = []
msg = ""
message_path =ConfigAPI().get_messages_file_path()
message_path_description = message_path.replace(".txt" , "_description.txt")

def read():
    global is_read
    print "fileis reading now."
    if not os.path.exists(message_path) or not os.path.exists(message_path_description):
        raise Exception("Messages files not exists.")

    with open(message_path_description, 'r') as f:
         for line in f.read().splitlines():
             if line != "":
                 line_description = line.split("#")
                 k, v = line_description[0].split("=")
                 details =line_description[0].split("=")
                 msg = details[0] + "="+ details[1]
                 list.append(msg)
                 old_msgs[str(k).strip()] =str(v).strip()
    is_read= True

def save():
    with open(message_path, 'w'): pass
    f = "ui_test"+ "="+ "hello"
    list.append(f)
    with open(message_path, 'a') as f:
     for key in list:
      print(key)
      f.write(format(key)+'\n')
      is_read =False