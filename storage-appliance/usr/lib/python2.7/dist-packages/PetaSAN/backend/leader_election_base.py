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


from time import sleep
from PetaSAN.core.common.log import logger
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.consul.api import ConsulAPI
from requests.exceptions import ConnectionError
from PetaSAN.core.cluster.configuration import configuration


# curl -v  http://localhost:8500/v1/kv/PetaSAN/Services/?recurse
# curl -v  http://localhost:8500/v1/kv/PetaSAN/Services/ClusterLeader

# need tp quote for params
# curl -v  "http://127.0.0.1:8500/v1/kv/PetaSAN/Services/ClusterLeader?index=0&wait=20s"
# curl -v  http://localhost:8500/v1/session/list
# curl -v  http://localhost:8500/v1/session/info/4264c593-5714-f034-cfa8-5df49c364724



CONNECTION_RETRY_TIMEOUT_SEC = 5
LOOP_SLEEP_SEC = 5

class LeaderElectionBase(object):

    def __init__(self,service_name,watch_timeout='20s'):
        self.service_name = service_name
        self.service_key  = ConfigAPI().get_consul_services_path() + service_name
        self.watch_timeout = watch_timeout
        self.session = '0'
        #self.session_name = ConfigAPI().get_leader_service_session_name()
        self.session_name = self.service_name
        self.leader = False

    def drop_old_sessions(self):
        logger.info("LeaderElectionBase dropping old sessions")
        node_name = configuration().get_node_info().name
        count = 0
        while True:
            sleep(10)
            try:
                ConsulAPI().drop_all_node_sessions(self.session_name,node_name)
                logger.info("LeaderElectionBase successfully dropped old sessions")
                break
            except Exception as e:
                logger.error("LeaderElectionBase exception dropping old sessions")
                pass
            count = count + 1
            if 30 <= count:
                break

    def run(self):
        self.drop_old_sessions()
        modify_index = '0'
        node_name = configuration().get_node_info().name
        while True:
            try:
                sleep(LOOP_SLEEP_SEC)
                if self.session == '0':
                    self.session =ConsulAPI().get_new_session_ID(self.session_name,node_name)
                kv = ConsulAPI().get_key_blocking(self.service_key,modify_index,self.watch_timeout)
                if kv:
                    modify_index = kv.ModifyIndex
                    if not hasattr(kv,'Session'):
                        # cluster key not locked
                        if not self.leader :
                            # we had no prev lock, attempt to lock
                            if ConsulAPI().lock_key(self.service_key, self.session, ''):
                                # lock successful, change state and call start action
                                self.leader = True
                                self.start_action()

                        else :
                            # we had a prev lock, change state and call stop action
                            self.leader = False
                            self.stop_action()

                    else:
                        # cluster key locked in consul
                        if self.leader:

                            if kv.Session == self.session:
                                if not self.health_check:
                                    logger.error("LeaderElectionBase health check failed")
                                    self.leader = False
                                    self.stop_action()
                                    # get a new session, this also drops old session if present
                                    self.session = ConsulAPI().get_new_session_ID(self.session_name,node_name)
                            else:
                                # kv.Session != self.session:
                                # we had a prev lock, but is actually locked by someone else
                                # change state and call stop action
                                self.leader = False
                                self.stop_action()



                        if self.leader and kv.Session != self.session:
                            # we had a prev lock, but is actually locked by someone else
                            # change state and call stop action
                            self.leader = False
                            self.stop_action()

                else:
                    # service key not found, attempt to lock it
                    if not self.leader :
                        if ConsulAPI().lock_key(self.service_key,  self.session, '') :
                            # lock successful, change state and call start action
                            self.leader = True
                            self.start_action()
                    else:
                        self.leader = False
                        self.stop_action()


            except ConnectionError:
                logger.error("LeaderElectionBase connection error")
                sleep(CONNECTION_RETRY_TIMEOUT_SEC)
            except Exception as e:
                logger.error("LeaderElectionBase exception")
                logger.error(e.message)
                sleep(CONNECTION_RETRY_TIMEOUT_SEC)
                if str(e.message).find("invalid session") > -1:
                    logger.error("LeaderElectionBase session is invalid")
                    self.stop_action()
                    try:
                        self.session = ConsulAPI().get_new_session_ID(self.session_name,node_name)
                        logger.info("LeaderElectionBase new session id created {}".format(self.session))
                    except:
                        logger.error("LeaderElectionBase connection error")
                        sleep(CONNECTION_RETRY_TIMEOUT_SEC)

    def is_leader(self) :
        return self.leader

    def quit_leader(self) :
        if not self.leader :
            return
        self.leader = False
        self.stop_action()
        ConsulAPI().unlock_key(self.service_key, self.session, '')
        return

    def start_action(self):
        logger.info("LeaderElectionBase start action")
        return

    def stop_action(self) :
        logger.info("LeaderElectionBase stop action")
        return

    def health_check(self) :
        return True


    def get_leader_node(self):

        try:
            consul_obj = ConsulAPI()
            kv = consul_obj.get_key(ConfigAPI().get_consul_services_path() + self.service_name)
            if kv is  None or not hasattr(kv,"Session"):
                return None

            sessions = consul_obj.get_sessions_dict()
            node_session = sessions.get(kv.Session,None)
            if not node_session:
                return  None
            return node_session.Node

        except Exception as e:
            pass

        return None



