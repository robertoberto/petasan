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

import os
from time import sleep
from PetaSAN.core.config.api import ConfigAPI
from flask import app

app.key_value_msgs = dict()
app.last_modify = ""
app.test_text = ""
app.is_completed_read = False


def gettext(msg_key, *args):
    if str(msg_key) is None or str(msg_key) == "":
        return ""

    args_list = str(msg_key).split("%")
    if len(args_list) > 1:
        msg_key = args_list[0]
        args = args_list[1:len(args_list)]
    new_last_modify = os.path.getmtime(ConfigAPI().get_messages_file_path())
    if str(app.last_modify) == str(new_last_modify):
        while False == app.is_completed_read:
            sleep(0.2)
        msg = str(__gettext(msg_key, False))
        if args:
            return msg.format(*args)
        return msg
    else:
        app.last_modify = str(new_last_modify)
        msg = str(__gettext(msg_key, True))
        if args:
            return msg.format(*args)
        return msg


def __gettext(key, read=True):
    if read:
        path = ConfigAPI().get_messages_file_path()
        with open(path, 'r') as f:
            for line in f.read().splitlines():
                if line.find("=")>-1:
                    k, v = line.split("=")
                    app.key_value_msgs[str(k).strip()] = str(v).strip()
                    app.is_completed_read = True

    if app.key_value_msgs.has_key("ui_test"):
        # Test mode
        return "!" + str(app.key_value_msgs.get(str(key), "@@" + str(key)))

    return str(app.key_value_msgs.get(str(key), str(key)))
