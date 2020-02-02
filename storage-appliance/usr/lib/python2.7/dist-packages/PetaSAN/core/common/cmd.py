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
import subprocess
from time import sleep
import signal
from PetaSAN.core.common.log import logger


def call_script(file_name):
    cmd = "python {} ".format(file_name)
    # print cmd
    return subprocess.call(cmd, shell=True)


# ----------------------------------------------------------------------------------------------------------------------

def call_cmd(cmd):
    if subprocess.call(cmd, shell=True) == 0:
        return True
    else:
        return False


# ----------------------------------------------------------------------------------------------------------------------

def call_cmd_2(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    ret = p.returncode

    if ret == 0:
        return True
    else:
        return False


# ----------------------------------------------------------------------------------------------------------------------

def exec_command(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    input = None
    stdout, stderr = p.communicate()

    return stdout, stderr


# ----------------------------------------------------------------------------------------------------------------------

def exec_command_ex(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    input = None
    stdout, stderr = p.communicate()
    ret = p.returncode
    #  stdout.splitlines()

    return ret, stdout, stderr


# ----------------------------------------------------------------------------------------------------------------------

def kill(name):
    out, err = exec_command(' pgrep  {}'.format(name))
    # Kill process.
    for pid in out.splitlines():
        logger.info("{} process pid is {}".format(name, pid))
        os.kill(int(pid), signal.SIGTERM)
        logger.info("Trying to stop {} process".format(name))
        sleep(3)
        try:
            os.kill(int(pid), 0)
        except Exception as ex:
            logger.info("{} process stopped".format(name))
            continue


# ----------------------------------------------------------------------------------------------------------------------

def kill_by_file_name(name):
    out, err = exec_command(' pgrep -f {}'.format(name))
    # Kill process.
    for pid in out.splitlines():
        logger.info("{} process is {}".format(name, pid))
        try:
            os.kill(int(pid), signal.SIGTERM)
            logger.info("Trying to stop {} process".format(name))
            sleep(3)
            os.kill(int(pid), 0)
        except Exception as ex:
            logger.info("{} process stopped".format(name))
            continue


# ----------------------------------------------------------------------------------------------------------------------
