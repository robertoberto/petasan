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


from ipaddr import  *


def get_subnet_base_ip(ip,mask):
    net = IPNetwork(ip + '/' + mask)
    return str(net.network)

def is_ip_in_subnet(ip,subnet_base_ip,mask):
    ip_addr = IPAddress(ip)
    net = IPNetwork(subnet_base_ip + '/' + mask)
    if ip_addr in net:
        return True
    return False

def get_address_count(ip_from,ip_to):
    ip = IPAddress(ip_from)
    ip_end = IPAddress(ip_to)
    count = 0
    while (ip + count) <= ip_end :
        count = count +1
    return count

class IPAddressGenerator :

    def __init__(self,ip_from,ip_to):
        self.ip_from = IPAddress(ip_from)
        self.ip_to = IPAddress(ip_to)
        self.index = 0

    def has_next(self):
        if (self.ip_from + self.index) <= self.ip_to :
            return True
        return False

    def get_next(self) :
        if not self.has_next() :
            return ''
        ret = str( self.ip_from + self.index )
        self.index = self.index +1
        return ret

