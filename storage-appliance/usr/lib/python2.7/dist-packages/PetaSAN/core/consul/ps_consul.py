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

from six.moves import urllib

import requests

from consul import base
from requests.adapters import HTTPAdapter
from requests.adapters import Retry

from PetaSAN.core.common.log import logger
from retrying import retry

__all__ = ['Consul']

REQUEST_TIMEOUT = 15
# retry failed requests after 1 2 4 8 16 32 sec
RETRY_BACKOFF = 1.0
RETRY_TOTAL = 6
RETRY_ADAPTER_PREFIX = 'http://127.0.0.1:8500/v1'
RETRY_ERROR_LIST = ["cluster leader", "rpc error"]


class RetryConsulException(Exception):
    pass


class HTTPClient(object):
    def __init__(self, host='127.0.0.1', port=8500, scheme='http',
                 verify=True, cert=None):
        self.host = host
        self.port = port
        self.scheme = scheme
        self.verify = verify
        self.cert = cert
        self.base_uri = '%s://%s:%s' % (self.scheme, self.host, self.port)
        self.session = requests.session()
        retry_adapter = HTTPAdapter(max_retries=Retry(total=RETRY_TOTAL, backoff_factor=RETRY_BACKOFF))
        self.session.mount(RETRY_ADAPTER_PREFIX, retry_adapter)

    def response(self, response):
        return base.Response(
            response.status_code, response.headers, response.text)

    def uri(self, path, params=None):
        uri = self.base_uri + path
        if not params:
            return uri
        return '%s?%s' % (uri, urllib.parse.urlencode(params))

    # stop_max_delay = 120000  -->  120 seconds = 2 minutes  max
    # wait_exponential_multiplier = 1000  -->  wait (2^i * 1000 ms) = (2^i * 1s) , on the i-th retry
    @retry(wait_exponential_multiplier=1000, stop_max_delay=120000)
    def get(self, callback, path, params=None):
        uri = self.uri(path, params)
        res = self.response(self.session.get(uri, verify=self.verify))

        if res is not None and res.code == 500 and "invalid session" not in res.body:
            for err in RETRY_ERROR_LIST:
                if str(res.body).find(err) > -1:
                    raise RetryConsulException()
        return callback(res)

    @retry(wait_exponential_multiplier=1000, stop_max_delay=120000)
    def put(self, callback, path, params=None, data=''):
        uri = self.uri(path, params)
        res = self.response(self.session.put(uri, data=data, verify=self.verify))

        if res is not None and res.code == 500 and "invalid session" not in res.body:
            for err in RETRY_ERROR_LIST:
                if str(res.body).find(err) > -1:
                    raise RetryConsulException()
        return callback(res)

    @retry(wait_exponential_multiplier=1000, stop_max_delay=120000)
    def delete(self, callback, path, params=None):
        uri = self.uri(path, params)
        res = self.response(self.session.delete(uri, verify=self.verify))
        if res is not None and res.code == 500 and "invalid session" not in res.body:
            for err in RETRY_ERROR_LIST:
                if str(res.body).find(err) > -1:
                    raise RetryConsulException()
        return callback(res)


class Consul(base.Consul):
    def connect(self, host, port, scheme, verify=True, cert=None):
        return HTTPClient(host, port, scheme, verify, cert)
