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

from PetaSAN.core.consul.ps_consul import RetryConsulException
from datetime import date, datetime
from requests import ConnectionError
from time import sleep
from consul import ConsulException
from PetaSAN.core.common.log import logger


from uuid import uuid1, uuid4
from flask.sessions import SessionInterface, SessionMixin
from PetaSAN.core.consul.base import BaseAPI
from PetaSAN.core.config.api import ConfigAPI
consul_session_key= ConfigAPI().get_consul_session_path()

class ConsulSession(SessionMixin):


    """Server-side session implementation.
    """

    def __init__(self,  sid, *args, **kwargs):
        self.sid = sid
        self.get_all_sessions()
        self.permanent= True
        pass

    def __getitem__(self, key):
        self.get_all_sessions()
        self.__dict__[key]
        return self.__dict__[key]

    def __setitem__(self, key, value):
        consul_base_api = BaseAPI()
        if self.sid =='-1':
            return

        try:
            consul_base_api.write_value("".join( [consul_session_key,self.sid,"/",key]),str(value))
        except ConnectionError:
            logger.error("Error on consul connection to set session.")
            sleep(1)

    def __delitem__(self, key):
        consul_base_api = BaseAPI()
        consul_base_api.delete_key("".join( [consul_session_key,self.sid,"/",key]))


    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def get(self, key,value):
        self.get_all_sessions()
        self.__dict__.get(key)
        if key == "_permanent":
            return  True
        return self.__dict__.get(key)

    def pop(self, key):
        self.__delitem__(key)
        return self.__dict__.pop(key)

    def clear(self):
        consul_base_api = BaseAPI()
        consul_base_api.delete_key("".join( [consul_session_key,self.sid,"/"]),True)

    def get_all_sessions(self):
        consul_base_api = BaseAPI()
        #self.data = {}
        try_count = 0
        status = False
        while status != True:
            try:
                session_data = consul_base_api.read_recurse("".join( [consul_session_key,self.sid,"/"]))
                if session_data:
                    for s in session_data:
                        self.__dict__[str(s['Key']).replace("".join( [consul_session_key,self.sid,"/"]),"")]= s['Value']
                status = True
            except ConnectionError:
                    logger.error("Error on consul connection")
                    sleep(1)

                    try_count +=1
            except ConsulException:
                    logger.error("Error on consul leader.")
                    sleep(1)
                    try_count +=1
            except RetryConsulException:
                    logger.error("Error on consul leader.")
                    sleep(1)
                    try_count +=3
            if try_count >2:
                self.sid= '-1'
                status = True
        return self.__dict__



class ConsulSessionInterface(SessionInterface):

    def __init__(self):
        pass

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = str(uuid4())
        else:
            consul_base_api = BaseAPI()
            _exp = consul_base_api.read_value("".join( [consul_session_key,sid,"/_exp"]))
            if _exp:
                if datetime.utcnow()> datetime.strptime(_exp,"%Y-%m-%d %H:%M:%S.%f"):
                    consul_base_api.delete_key("".join( [consul_session_key,sid,"/"]))
                    sid = str(uuid4())


        return ConsulSession(sid,"")

    def save_session(self, app, session, response):
        try:
            domain = self.get_cookie_domain(app)
            consul_base_api = BaseAPI()
            if not session:
                consul_base_api.delete_key("".join( [consul_session_key,self.sid,"/"]))
                response.delete_cookie(
                    app.session_cookie_name, domain=domain)
                return
            else:
                if session.sid =='-1':
                    raise ConnectionError()

            cookie_exp = self.get_expiration_time(app, session)
            if session.sid !='-1':
                consul_base_api.write_value("".join( [consul_session_key,session.sid,"/_exp"]),str(cookie_exp))
            response.set_cookie(
                app.session_cookie_name, session.sid,
                 httponly=True, domain=domain)
        except ConnectionError:
            logger.error("Error on consul connection to save session")
            response.delete_cookie(
                    app.session_cookie_name, domain=domain)
            sleep(1)