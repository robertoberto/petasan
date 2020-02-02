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

import shutil
import pexpect
import json
import os

from PetaSAN.core.common.log import logger



# import pexpect
import os
import subprocess

PROMPT_NEW_KEY = 'Are you sure you want to continue connecting'
PROMPT_PASSWORD = 'password:'
OPTIONS = ' -o StrictHostKeyChecking=no '
#OPTIONS = ''



class ssh(object):


    """
    Create user public and private keys

    """
    def create_id(self,overwrite):
        id_rsa_pub_file = os.path.expanduser(u'~/.ssh/id_rsa.pub')
        id_rsa_file = id_rsa_pub_file.split('.pub')[0]
        if not overwrite and os.path.exists(id_rsa_file):
            return
        elif overwrite and os.path.exists(id_rsa_file):
            os.remove(id_rsa_file)
            os.remove(id_rsa_pub_file)

        #cmd =  [ 'ssh-keygen','-t','rsa','-N',"",'-f',id_rsa_file ]
        #ret = subprocess.call(cmd)

        cmd = 'ssh-keygen -t rsa -N ""  -f ' + id_rsa_file
        if subprocess.call(cmd,shell=True) ==0:
            return  True


        return False


    """
     Copy our public key to host non-interactively
    """

    def copy_id_to_host(self,hostname,password):

        try :
            p=pexpect.spawn('ssh-copy-id  ' + hostname)
            ret = p.expect([PROMPT_NEW_KEY,PROMPT_PASSWORD,pexpect.EOF])

            if ret == 0:
                # first time, asking us to accept server cetificate
                p.sendline('yes')
                ret =p.expect([PROMPT_NEW_KEY,PROMPT_PASSWORD,pexpect.EOF])
            if ret ==1:
                # need to provide password, we have not copied keys yet
                p.sendline(password)
                p.expect(pexpect.EOF)
            elif ret ==2:
                # either got key or connection timeout"
                pass

            if p.before.find('Number of key(s) added') != -1:
                return True

            if p.before.find('already exist') != -1:
                return True

        except Exception as e:
            pass


        return False


    """
        Copy our public key from host non-interactively
    """
    def copy_public_key_from_host(self,hostname,password):

        id_rsa_pub_file = os.path.expanduser('~/.ssh/id_rsa.pub')
        if os.path.exists(id_rsa_pub_file):
            os.remove(id_rsa_pub_file)
        if os.path.exists(os.path.expanduser('~/.ssh/id_rsa')):
            os.remove(os.path.expanduser('~/.ssh/id_rsa'))
        if os.path.exists(os.path.expanduser('~/.ssh/authorized_keys')):
            os.remove(os.path.expanduser('~/.ssh/authorized_keys'))

        cmd = 'scp ' + OPTIONS + ' root@' + hostname + ':' + id_rsa_pub_file + ' ' + id_rsa_pub_file

        try:
            p=pexpect.spawn(cmd)
            ret = p.expect([PROMPT_NEW_KEY,PROMPT_PASSWORD,pexpect.EOF])

            if ret == 0:
                # first time, asking us to accept server cetificate
                p.sendline('yes')
                ret =p.expect([PROMPT_NEW_KEY,PROMPT_PASSWORD,pexpect.EOF])

            if ret ==1:
                # need to provide password, we have not copied keys yet
                p.sendline(password)
                p.expect(pexpect.EOF)

            if p.before.find('100%') != -1:
                return True

        except Exception as e:
            pass

        return False

    def create_authorized_key_file(self):
        id_rsa_pub_file = os.path.expanduser('~/.ssh/id_rsa.pub')
        authorized_key = os.path.expanduser('~/.ssh/authorized_keys')
        # authorized_key
        shutil.copy(id_rsa_pub_file,authorized_key)


    """
        Copy our private key from host non-interactively
    """
    def copy_private_key_from_host(self,hostname,password):

        id_rsa_pub_file = os.path.expanduser('~/.ssh/id_rsa')
        cmd = 'scp ' + OPTIONS + ' root@' + hostname + ':' + id_rsa_pub_file + ' ' + id_rsa_pub_file

        try:
            p=pexpect.spawn(cmd)
            ret = p.expect([PROMPT_NEW_KEY,PROMPT_PASSWORD,pexpect.EOF])

            if ret == 0:
                # first time, asking us to accept server cetificate
                p.sendline('yes')
                ret =p.expect([PROMPT_NEW_KEY,PROMPT_PASSWORD,pexpect.EOF])

            if ret ==1:
                # need to provide password, we have not copied keys yet
                p.sendline(password)
                p.expect(pexpect.EOF)

            if p.before.find('100%'):
                return True

        except Exception as e:
            pass

        return False


    def copy_file_to_host(self,hostname,file):
        cmd = 'scp ' + OPTIONS + ' ' +file + ' root@' + hostname + ':' + file

        if subprocess.call(cmd,shell=True) == 0:
            return True
        return False

    def copy_file_from_host(self,hostname,file):
        cmd = 'scp ' + OPTIONS +' root@' + hostname + ':' + file + ' ' + file

        if subprocess.call(cmd,shell=True) == 0:
            return True
        return False


    def copy_dir_to_host(self,hostname,dir):
        dest_dir = os.path.split(dir)[0]
        cmd = 'scp  -r ' + OPTIONS + ' ' +dir+ ' root@' + hostname + ':' + dest_dir

        if subprocess.call(cmd,shell=True) == 0:
            return True
        return False

    def copy_dir_from_host(self,hostname,dir):
        dest_dir = os.path.split(dir)[0]
        cmd = 'scp -r ' + OPTIONS +' root@' + hostname + ':' + dir+ ' ' + dest_dir

        if subprocess.call(cmd,shell=True) == 0:
            return True
        return False



    def write_string_to_file(self,string, hostname,file):
        cmd = '\"cat <<EOT > '
        cmd += file
        cmd += '\n' + string + '\n'
        cmd += 'EOT\"'
        ret = self.call_command(hostname,cmd)
        return ret


    def exec_command(self,hostname,cmd):
        p = subprocess.Popen(" ".join(['ssh',OPTIONS, 'root@'+hostname, cmd]),shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE)
        stdout,stderr = p.communicate()

        #  stdout.splitlines()
        return stdout,stderr


    def call_command(self,hostname,cmd,time_out = -1):
        time_out_opt = ""
        if time_out >-1:
            time_out_opt  = " -o ConnectTimeout={} ".format(time_out)

        cmd = 'ssh '+OPTIONS+time_out_opt+ ' root@'+hostname + " " +cmd
        print cmd
        if subprocess.call(cmd,shell=True) == 0:
            return True
        return False


    def check_ssh_connection(self,host):
        cmd = "ssh {} root@{}  ls".format(OPTIONS,host)
        print cmd
        if subprocess.call(cmd,shell=True) == 0:
            return True
        return False



    def get_remote_object(self,hostname,cmd):

        (stdout,stderr) = self.exec_command(hostname,cmd)
        if stderr:
            return None

        try:
            obj = json.loads(stdout)
            return obj
        except:
            return None




