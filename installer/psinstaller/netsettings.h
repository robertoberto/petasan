/*
 Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
 Copyright (C) 2019 PetaSAN www.petasan.org


 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU Affero General Public License
 as published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU Affero General Public License for more details.
 */

#ifndef NETSETTINGS_H
#define NETSETTINGS_H

class NetSettings
{
public:

    NetSettings() {}
    NetSettings(QString hostname,QString iface,QString ip,QString mask,QString gateway,QString dns,QString vlan) {
        this->hostname = hostname;
        this->iface = iface;
        this->ip = ip;
        this->mask = mask;
        this->gateway = gateway;
        this->dns = dns;
        this->vlan = vlan;

    }

    QString hostname;
    QString iface;
    QString ip;
    QString mask;
    QString gateway;
    QString dns;
    QString vlan;


};


#endif // NETSETTINGS_H
