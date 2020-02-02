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

#ifndef ZONEINFO
#define ZONEINFO


#include <QString>

class ZoneInfo
{
public:

    ZoneInfo() {}
    ZoneInfo(QString country,QString countryCode,QString zone ) {
        this->country = country;
        this->countryCode = countryCode;
        this->zone = zone;
    }

    QString country;
    QString countryCode;
    QString zone;

};


#endif // ZONEINFO

