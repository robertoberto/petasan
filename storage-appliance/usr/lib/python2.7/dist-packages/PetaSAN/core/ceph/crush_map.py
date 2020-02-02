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

from PetaSAN.core.ceph.ceph_authenticator import CephAuthenticator

from PetaSAN.core.common.cmd import call_cmd, exec_command_ex
from PetaSAN.core.common.CustomException import CephException, CrushException
from PetaSAN.core.common.log import logger
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.core.config.api import ConfigAPI
from datetime import *
import random
import string

class CrushMap:

    CRUSH_SAVE_PATH = ConfigAPI().get_crush_save_path()

    def __init__(self):

        self.types = [-1 for i in range(20)]
        self.buckets = []
        self.rules = {}
        self.device_class = {}
        self.device_weight = {}

        self.lines_tunables = []
        self.lines_devices = []
        self.lines_types = []
        self.lines_buckets = []
        self.lines_rules = []


    def _decode_types(self):
        max_index = 0
        for line in self.lines_types :
            if line.endswith('type'):
                continue
            tokens = line.split()
            self.types[int(tokens[1])] = tokens[2]
            if int(tokens[1]) > max_index :
                max_index = int(tokens[1])
        self.types =  self.types[:max_index+1]
      
    def _decode_buckets(self):
        bucket = None
        for line in self.lines_buckets :
            if line.endswith('{') :
                bucket = {}
                bucket['items'] = []
                bucket['class_ids'] =  {}
                tokens = line.split()
                type = tokens[0]
                type_id = self.types.index(type)
                bucket['type_id'] = type_id
                bucket['name'] = tokens[1]

            elif line.startswith('alg') :
                tokens = line.split()
                bucket['alg'] = tokens[1]

            elif line.startswith('hash') :
                tokens = line.split()
                bucket['hash'] = int(tokens[1])

            elif line.startswith('item') :
                tokens = line.split()

                if len(tokens) == 4 and tokens[1].startswith('osd.') :
                    # osd, append class and weight info
                    self.device_weight[tokens[1]] = tokens[3]

                    if self.device_class.has_key(tokens[1]):
                        item = tokens[1] + '#' + self.device_class[tokens[1]] + '#' + self.device_weight[tokens[1]]
                    else:
                        item = tokens[1] + '#' + 'class not defined' + '#' + self.device_weight[tokens[1]]

                    bucket['items'].append(item)
                else:
                    bucket['items'].append(tokens[1])


            elif line.startswith('id') :
                tokens = line.split()
                id = int(tokens[1])
                if tokens[2] == 'class' :
                    bucket['class_ids'][tokens[3]] = id
                else :
                    bucket['id'] = id

                bucket['hash'] = int(tokens[1])


            elif line.startswith('}') :
                self.buckets.append(bucket)


        #print(self.buckets)


    def _decode_rules(self):

        name = None
        body = None
        for line in self.lines_rules :
            if line.startswith('rule') :
                tokens = line.split()
                name = tokens[1]
                body = '{\n'
                continue

            if line.startswith('}') :
                body += '}'
                self.rules[name] = body
                continue

            body += line + '\n'

        #print self.rules


    def _decode_device_class(self):
        for line in self.lines_devices :
            if not line.startswith('device') :
                continue
            tokens = line.split()

            if len(tokens) != 5 :
                continue

            if not tokens[2].startswith('osd') or not tokens[3].startswith('class') :
                continue
            self.device_class[tokens[2]] = tokens[4]


    def _get_rule_ids(self):
        ids = []
        for rule in self.rules :
            body = self.rules[rule]
            id = self._get_rule_id(body)
            if id :
                ids.append(id)
        return ids

    def _get_rule_id(self,body):
        lines = body.splitlines()
        for line in lines :
            if line.startswith('id') :
                tokens = line.split()
                if len(tokens) < 2 :
                    continue
                return tokens[1]
        return None

    def _get_rule_class(self,body):
        lines = body.splitlines()
        for line in lines :
            line.strip()
            if line.startswith('#') :
                continue
            if 'step' in line and 'take' in line and 'class' in line:
                tokens = line.split()
                index = tokens.index('class')
                if index+1 < len(tokens):
                    return tokens[index+1]
        return None


    def _encode_buckets(self) :
        self.lines_buckets = []
        bucket_names = set()

        for bucket in self.buckets:
            
            # duplicate name check
            if bucket['name'] in  bucket_names:
                logger.error('Crush duplicate bucket name:' + bucket['name'])
                raise CrushException(CrushException.DUPLICATE_BUCKET_NAME,'Duplicate bucket name')
            bucket_names.add( bucket['name'])

            type = self.types[bucket['type_id'] ]
            self.lines_buckets.append(type + ' ' + bucket['name'] + ' {')
            self.lines_buckets.append('id ' + str(bucket['id']) )

            if bucket.has_key('class_ids'):
                for c in   bucket['class_ids']:
                    self.lines_buckets.append('id ' + str( bucket['class_ids'][c]) + ' class ' +c  )

            self.lines_buckets.append('alg ' + bucket['alg'] )
            self.lines_buckets.append('hash ' + str(bucket['hash']) )

            if 'items' in bucket:
                for item in  bucket['items']:
                    if item.startswith('osd') :
                        # osd
                        tokens = item.split('#')
                        osd_item = 'item ' + tokens[0]
                        if tokens[0] in self.device_weight :
                            osd_item += ' weight ' +  self.device_weight[tokens[0]]
                        self.lines_buckets.append(osd_item)
                    else:
                        self.lines_buckets.append('item ' + item)

            self.lines_buckets.append('}')


    def _encode_rules(self):
        self.lines_rules = []
        for name in self.rules:
            self.lines_rules.append('rule ' + name +' ')
            body = self.rules[name]
            self.lines_rules += body.splitlines()


    def _get_rand_string(self,n):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))


    def _read_file_lines(self,backup=False):
        # Get which ceph user is using this function & get his keyring file path #
        ceph_auth = CephAuthenticator()

        call_cmd('mkdir -p ' + self.CRUSH_SAVE_PATH )
        cluster_name = configuration().get_cluster_name()

        rand = self._get_rand_string(6)
        bin_file = self.CRUSH_SAVE_PATH + 'crushmap-tmp-'+ rand + '.bin'
        txt_file = self.CRUSH_SAVE_PATH + 'crushmap-tmp-'+ rand + '.txt'

        cmd = 'ceph osd getcrushmap -o ' + bin_file + ' ' + ceph_auth.get_authentication_string() + ' --cluster ' + cluster_name
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            if stderr and ('Connection timed out' in stderr or 'error connecting' in stderr):
                logger.error('Error in Ceph Connection cmd:' + cmd)
                raise CephException(CephException.CONNECTION_TIMEOUT,'Connection Timeout Error')

            logger.error('General error in Ceph cmd:' + cmd + ' error:' + stderr)
            raise CephException(CephException.GENERAL_EXCEPTION,'General Ceph Error')

        cmd = 'crushtool -d ' +  bin_file + ' -o ' + txt_file
        if not call_cmd(cmd):
            raise CrushException(CrushException.DECOMPILE,'Crush Decompile Error')

        with open(txt_file, 'r') as f:
            lines = f.readlines()
        lines = [line.strip() for line in lines]

        section = 'start'
        # for section tags see src/crush/CrushCompiler.cc decompile

        for line in lines:
            if len(line) == 0:
                continue
            if line.startswith('# begin crush map'):
                section = 'tunables'
                continue
            elif line.startswith('# devices'):
                section = 'devices'
                continue
            elif line.startswith('# types'):
                section = 'types'
                continue
            elif line.startswith('# buckets'):
                section = 'buckets'
                continue
            elif line.startswith('# rules'):
                section = 'rules'
                continue

            elif line.startswith('# choose_args'):
                section = 'end'
                break
            elif line.startswith('# end crush map'):
                section = 'end'
                break

            if section == 'tunables':
                self.lines_tunables.append(line)
            elif section == 'devices':
                self.lines_devices.append(line)
            elif section == 'types':
                self.lines_types.append(line)
            elif section == 'buckets':
                self.lines_buckets.append(line)
            elif section == 'rules':
                self.lines_rules.append(line)

        if backup:
            self._backup(txt_file)

        call_cmd('rm ' + txt_file )
        call_cmd('rm ' + bin_file )



    def _backup(self,crush_file):

        stamp = datetime.now().strftime('%Y%m%d-%H:%M:%S')
        backup_name = 'crushmap-' + stamp + '.txt'
        backup_path = self.CRUSH_SAVE_PATH + backup_name
        # backup on filesystem
        cmd = 'cp ' + crush_file + ' ' + backup_path
        call_cmd(cmd)
        # backup to consul
        cmd = 'consul kv put PetaSAN/crush/' + backup_name + ' @' + backup_path
        call_cmd(cmd)


    def _get_backup_file_name(self):
        t = datetime.now().strftime('%Y%m%d-%H:%M:%S')
        return self.CRUSH_SAVE_PATH + 'crushmap-' + t + '.txt'


    def _write_file_lines(self):

        rand = self._get_rand_string(6)
        bin_file = self.CRUSH_SAVE_PATH + 'crushmap-tmp-'+ rand + '.bin'
        txt_file = self.CRUSH_SAVE_PATH + 'crushmap-tmp-'+ rand + '.txt'

        with open(txt_file, 'w') as f:

            for line in self.lines_tunables:
                 f.writelines(line +'\n')
            f.writelines('\n')
            for line in self.lines_devices:
                 f.writelines(line +'\n')
            f.writelines('\n')
            for line in self.lines_types:
                 f.writelines(line +'\n')
            f.writelines('\n')
            for line in self.lines_buckets:
                 f.writelines(line +'\n')
            f.writelines('\n')
            for line in self.lines_rules:
                 f.writelines(line +'\n')
            f.writelines('\n')


        cmd = 'crushtool -c ' + txt_file + ' -o ' + bin_file
        if not call_cmd(cmd):
            raise CrushException(CrushException.COMPILE,'Crush Compile Error')

        cluster_name = configuration().get_cluster_name()
        cmd = 'ceph osd setcrushmap -i ' + bin_file + ' --cluster ' + cluster_name
        ret, stdout, stderr = exec_command_ex(cmd)
        if ret != 0:
            if stderr and ('Connection timed out' in stderr or 'error connecting' in stderr):
                logger.error('Error in Ceph Connection cmd:' + cmd)
                raise CephException(CephException.CONNECTION_TIMEOUT,'Connection Timeout Error')

            logger.error('General error in Ceph cmd:' + cmd + ' error:' + stderr)
            raise CephException(CephException.GENERAL_EXCEPTION,'General Ceph Error')

        call_cmd('rm ' + txt_file )
        call_cmd('rm ' + bin_file )


    def read(self,backup=False):

        self._read_file_lines(backup)
        self._decode_device_class()
        self._decode_types()
        self._decode_buckets()
        self._decode_rules()


    def write(self):
        self._encode_rules()
        self._encode_buckets()
        self._write_file_lines()


    def get_bucket_types(self) :
        return self.types


    def get_buckets(self) :
        return self.buckets


    def set_buckets(self,buckets) :
        self.buckets = buckets


    def get_rules(self):
        return self.rules


    def add_rule(self,name,body):
        if self.rules.has_key(name):
            logger.error('add rule error, rule name ' + name + ' already exists')
            raise CrushException(CrushException.DUPLICATE_RULE_NAME,'Duplicate rule name')

        ids = self._get_rule_ids()
        id = self._get_rule_id(body)
        if id in ids :
            logger.error('add rule error, rule id ' + id + ' already exists')
            raise CrushException(CrushException.DUPLICATE_RULE_ID,'Duplicate rule id')

        dev_class = self._get_rule_class(body)
        if dev_class:
            if dev_class not in self.device_class.values():
                logger.error('add rule error, device class ' + dev_class + ' does not exist')
                raise CrushException(CrushException.DEVICE_TYPE_NOT_EXISTS,'Device type does not exist')

        self.rules[name] = body


    def update_rule(self,name,body):
        if not self.rules.has_key(name):
            logger.error('edit rule error, rule name ' + name + ' not found')
            raise CrushException(CrushException.RULE_NOT_FOUND,'Rule not found')

        id_old = self._get_rule_id( self.rules[name] )
        id_new = self._get_rule_id(body)

        if id_new != id_old:
            ids = self._get_rule_ids()
            if id_new in ids :
                logger.error('update rule error, rule id ' + id_new + ' already exists')
                raise CrushException(CrushException.DUPLICATE_RULE_ID,'Duplicate rule id')

        self.rules[name] = body


    # def get_next_rule_id(self):
    #     next = 0
    #     ids = self._get_rule_ids()
    #     for id in ids :
    #         if next < int(id) :
    #             next = int(id)
    #     return str(next+1)

    def get_next_rule_id(self):
        ids = self._get_rule_ids()
        next_id = 0
        ids_set = set(ids)
        while True:
            if str(next_id) not in ids_set:
                return str(next_id)
            next_id += 1
        return str(next_id)


    def delete_rule(self,name):
        if not self.rules.has_key(name):
            logger.error('delete rule error, rule name ' + name + ' not found')
            raise CrushException(CrushException.RULE_NOT_FOUND,'Rule not found')
        del self.rules[name]


