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

#include "ipvalidator.h"
#include <QStringList>

IpValidator::IpValidator()
{
}


bool IpValidator::validateIp(QString ip){
    if( ip == NULL || ip.isEmpty() )
        return false;
    QStringList slist = ip.split(".");
    if( slist.size() != 4 )
        return false;
    for(int i=0; i<4; i++) {
        QString s = slist[i];
        if( s == NULL || s.isEmpty() )
            return false;
        bool ok;
        int val = s.toInt(&ok);
        if(!ok || val<0 || val>255)
         return false;
    }



    return true;
}

bool IpValidator::validateMask(QString mask) {

    if( mask == NULL || mask.isEmpty() )
        return false;

    int validMask = 0xffffffff;
    for(int i=0 ; i < 31; i++) {
        validMask = validMask << 1;
        int byte4 = (validMask & 0xff000000) >> 24;
        int byte3 = (validMask & 0x00ff0000) >> 16;
        int byte2 = (validMask & 0x0000ff00) >> 8;
        int byte1 = (validMask & 0x000000ff);
        QString s;
        s  = QString::number(byte4) + ".";
        s += QString::number(byte3) + ".";
        s += QString::number(byte2) + ".";
        s += QString::number(byte1);

        if( mask.compare(s) == 0)
            return true;
    }
    return false;
}
