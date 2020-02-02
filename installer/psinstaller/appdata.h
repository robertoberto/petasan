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

#ifndef APPDATA_H
#define APPDATA_H

#include <QString>
#include "diskinfo.h"
#include "netsettings.h"

class AppData
{
public:
    //QString device;
    DiskInfo di;
    NetSettings ns;
    QString zone;

    // upgrade support
    QString prev_install_disk;
    QString prev_install_version;
    bool can_upgrade;
    bool new_install;


    AppData();

};

#endif // APPDATA_H
