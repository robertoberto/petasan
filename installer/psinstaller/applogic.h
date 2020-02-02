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

#ifndef APPLOGIC_H
#define APPLOGIC_H

#include <QVector>
#include <QTextBrowser>
#include "diskinfo.h"
#include "ifinfo.h"
#include "zoneinfo.h"
#include "netsettings.h"


#define SCRIPT_BASE "/root/scripts/"
#define SCRIPT_DETECT_DISKS SCRIPT_BASE "detect-disks.sh"
#define SCRIPT_DETECT_IFS SCRIPT_BASE "detect-interfaces.sh"
#define SCRIPT_DETECT_INSTALL_DEVICE SCRIPT_BASE "detect-install-device.sh"
#define SCRIPT_EJECT_DEVICE SCRIPT_BASE "eject-device.sh"

#define SCRIPT_S1_FORMAT_DISK SCRIPT_BASE "s1-format-disk.sh"
#define SCRIPT_S2_INSTALL_ROOTFS SCRIPT_BASE "s2-install-rootfs.sh"
#define SCRIPT_S3_SET_TIME SCRIPT_BASE "s3-set-time.sh"
#define SCRIPT_S4_CONFIGURE_NETWORK SCRIPT_BASE "s4-configure-network.sh"
#define SCRIPT_S5_CREATE_INITRD SCRIPT_BASE "s5-create-initrd.sh"
#define SCRIPT_S6_INSTALL_BOOTLOADER SCRIPT_BASE "s6-install-bootloader.sh"
#define SCRIPT_S7_POST_INSTALL SCRIPT_BASE "s7-post-install.sh"

#define ZONE_INFO_FILE "/usr/share/zoneinfo/zone.tab"

#define MIN_DISK_SIZE_GIGS 64


// upgrade scripts


#define USCRIPT_BASE "/root/scripts/upgrade/"

#define USCRIPT_DETECT_PREV_INSTALL_DISK USCRIPT_BASE "get_ps_disk.sh"
#define USCRIPT_DETECT_PREV_INSTALL_VERSION USCRIPT_BASE "get_ps_version.sh"

#define USCRIPT_U1_PRE_INSTALL  "u1-pre-install.sh"
#define USCRIPT_U2_FORMAT_DISK   "u2-format-disk.sh"
#define USCRIPT_U3_INSTALL_ROOTFS "u3-install-rootfs.sh"
#define USCRIPT_U4_CREATE_INITRD  "u4-create-initrd.sh"
#define USCRIPT_U5_INSTALL_BOOTLOADER  "u5-install-bootloader.sh"
#define USCRIPT_U6_POST_INSTALL  "u6-post-install.sh"





class AppLogic
{
public:
    AppLogic();
    QVector<DiskInfo> DetectDisks();
    QVector<IFInfo> DetectInterfaces();
    QVector<ZoneInfo> ReadZones();
    //NetSettings getNetSettings();
	QString getInstallDevice();

	//void setConsole(QTextBrowser* console) { this->console = console; }
	void setCallBack(bool (*callback)(QString,int) ) { this->callback = callback; }

    void formatDisk(QString device);
    void installRootFS();
    void setTime(QString zone);
    void configureNetwork(NetSettings ns);
    void createInitrd();
	void installBootLoader(QString device);
	void postInstall();
	void ejectDevice(QString device);


    // upgrade support
    QString getPrevInstallDisk();
    QString getPrevInstallVersion();
    bool canUpgrade(QString prev_version);

    void u_preInstall(QString device,QString prev_version);
    void u_formatDisk(QString device,QString prev_version);
    void u_installRootFS(QString prev_version);
    void u_createInitrd(QString prev_version);
    void u_installBootLoader(QString device,QString prev_version);
    void u_postInstall(QString prev_version);



	void executeScript(QString path);


protected:

    QString scriptPath;
	//QTextBrowser* console;
	bool (*callback)(QString,int);




};

#endif // APPLOGIC_H
