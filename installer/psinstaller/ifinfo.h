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

#ifndef IFINFO_H
#define IFINFO_H

#include <QString>

class IFInfo {

public:

    IFInfo() {
    }

    IFInfo(QString iface,QString mac,QString pci,QString model) {
        this->iface = iface;
        this->mac = mac;
        this->pci = pci;
        this->model = model;
    }



    QString iface;
    QString mac;
    QString pci;
    QString model;




};


#endif // IFINFO_H
