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
from PetaSAN.backend.leader_election_base import LeaderElectionBase
from PetaSAN.core.cluster.sharedfs import SharedFS
import subprocess
from time import sleep


SERVICE_NAME = 'ClusterLeader'


class ClusterLeader(LeaderElectionBase):

    def __init__(self):
        super(ClusterLeader,self).__init__(SERVICE_NAME)
        self.counter = 0


    def start_action(self):
        logger.info('ClusterLeader start action')
        SharedFS().block_till_mounted()
        logger.info('ClusterLeader starting services')
        subprocess.call('/opt/petasan/scripts/stats-setup.sh',shell=True)
        subprocess.call('/opt/petasan/scripts/stats-start.sh',shell=True)

        subprocess.call('systemctl start petasan-notification',shell=True)
        return


    def stop_action(self) :
        logger.info('ClusterLeader stop action')
        subprocess.call('/opt/petasan/scripts/stats-stop.sh',shell=True)

        subprocess.call('systemctl stop petasan-notification',shell=True)
        return



    def health_check(self) :
        self.counter = self.counter+1
        if self.counter%10 != 0:
            return True

        if not self.is_service_running('carbon-cache'):
            logger.info('ClusterLeader re-starting services')
            self.stop_action()
            sleep(30)
            self.start_action()

        # sleep(30)
        # if not self.is_service_running("carbon-cache"):
        #    return False

        return True



    def is_service_running(self,service):
        cmd = '/bin/systemctl status ' + service
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        if '(running)' in str(out):
            return True
        return False
