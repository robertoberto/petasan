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

#ifndef DISKINFO_H
#define DISKINFO_H

#include <QString>

class DiskInfo
{
public:

    DiskInfo() {}
    DiskInfo(QString device,QString size,QString type,QString ssd,QString vendor,QString model,QString serial) {
        this->device = device;
        this->size = size;
        this->type = type;
        this->ssd = ssd;
        this->model = model;
        this->serial = serial;
    }

    QString device;
    QString size;
    QString type;
    QString ssd;
    QString vendor;
    QString model;
    QString serial;
};


#endif // DISKINFO_H
