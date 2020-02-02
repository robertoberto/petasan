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

#include "applogic.h"
#include <QProcess>

#include <QtDebug>
#include <QApplication>
#include <QThread>
#include <QScrollBar>
#include <QDateTime>
#include <QFile>
#include <QDir>
#include <QTextStream>

#include <unistd.h>

#include "diskinfo.h"

AppLogic::AppLogic()
{
	//console = NULL;
	callback = NULL;
}

 QVector<IFInfo> AppLogic::DetectInterfaces()
 {
     QVector<IFInfo> ifs;
     QString script = SCRIPT_DETECT_IFS;

     QProcess p;
     p.start(script);

     if (p.waitForStarted(-1)) {
         while(p.waitForReadyRead(-1)) {

             QByteArray byteArray = p.readAllStandardOutput();
             qDebug() << " detect-interfaces output is " << QString(byteArray);
             QStringList strLines = QString(byteArray).split("\n");

             foreach (QString line, strLines){
                 IFInfo ifi;
                 QStringList tokens = line.split(",");
                 foreach (QString token, tokens){
                     QStringList kv = token.split("=");
                     if( kv.size() == 2 ) {
                         QString key = kv[0];
                         key = key.trimmed();
                         QString val = kv[1];


                         if( key.compare( "device",Qt::CaseInsensitive) == 0 )
                             ifi.iface = val;
                           else if( key.compare( "mac",Qt::CaseInsensitive) == 0 )
                             ifi.mac = val;
                         else if( key.compare( "pci",Qt::CaseInsensitive) == 0 )
                             ifi.pci = val;
                         else if( key.compare( "model",Qt::CaseInsensitive) == 0 )
                             ifi.model = val;
                      }

                 }

                 if( ifi.iface.length() != 0 )
                     ifs.append(ifi);
             }

             //if ( p.state() == QProcess::NotRunning )
             //    break;

         }
     }


     return ifs;
 }

QVector<DiskInfo> AppLogic::DetectDisks()
{

    QVector<DiskInfo> disks;

    QString script = SCRIPT_DETECT_DISKS;
    QProcess p;
    p.start(script);

    if (p.waitForStarted(-1)) {
        while(p.waitForReadyRead(-1)) {

            QByteArray byteArray = p.readAllStandardOutput();
            qDebug() << " detect-disks output is " << QString(byteArray);
            QStringList strLines = QString(byteArray).split("\n");

            foreach (QString line, strLines){
                DiskInfo di;
                QStringList tokens = line.split(",");
                foreach (QString token, tokens){
                    QStringList kv = token.split("=");
                    if( kv.size() == 2 ) {
                        QString key = kv[0];
                        key = key.trimmed();
                        QString val = kv[1];


                        if( key.compare( "device",Qt::CaseInsensitive) == 0 )
                            di.device = val;
                        else if( key.compare( "size",Qt::CaseInsensitive) == 0 ) {
                            // 512 byte sectors
                            qint64 sectors = val.toLongLong();

                            int gbytes = sectors / 2 / 1024 / 1024;
                            if( gbytes < 1024 ) {
                                di.size = QString::number(gbytes) + " G";
                            }
                            else {
                                double tbytes = ((double)gbytes) / 1024.0;
                                di.size = QString::number(tbytes,'f',2) + " T";
                            }

                        }

                        else if( key.compare( "bus",Qt::CaseInsensitive) == 0 )
                            di.type = val;
                        else if( key.compare( "ssd",Qt::CaseInsensitive) == 0 )
                            di.ssd = val;
                        else if( key.compare( "vendor",Qt::CaseInsensitive) == 0 )
                            di.vendor = val;
                        else if( key.compare( "model",Qt::CaseInsensitive) == 0 )
                            di.model = val;
                        else if( key.compare( "serial",Qt::CaseInsensitive) == 0 )
                            di.serial = val;


                    }

                }

                if( di.device.length() != 0 )
                    disks.append(di);
            }

            //if ( p.state() == QProcess::NotRunning )
            //    break;

        }
    }



    return disks;
}

QString AppLogic::getInstallDevice() {
	QString device = "";
	QString script = SCRIPT_DETECT_INSTALL_DEVICE;
	QProcess p;
	p.start(script);

	if (p.waitForStarted(-1)) {
		while( p.waitForReadyRead(-1) )
		{
			QByteArray byteArray = p.readAllStandardOutput();
			QStringList strLines = QString(byteArray).split("\n");
			if ( 0 < strLines.size() ) {
				device = strLines.at(0).trimmed();
			}
			break;
		}
	}

	return device;
}

void AppLogic::executeScript(QString script) {

    qApp->processEvents();
    //usleep( 2000 * 1000);

    QByteArray ba = script.toLatin1();
    char* script_c = ba.data();

#define BUFF_SIZE 800
    char buff[BUFF_SIZE];

    FILE* fp;
    fp = popen(script_c,"r");
    if ( fp == NULL )
        return;

    while( fgets( buff,BUFF_SIZE, fp )  )
    {
		if(  callback != NULL ) {
			bool ret = (*callback)(QString(buff),0);
		 }
    }

    pclose( fp );

}




void AppLogic::formatDisk(QString device) {
    QString script = SCRIPT_S1_FORMAT_DISK;
    script +=  QString(" ") + device;
	executeScript(script);
}


void AppLogic::installRootFS() {
    QString script = SCRIPT_S2_INSTALL_ROOTFS;
	executeScript(script);
}


void AppLogic::setTime(QString zone) {
    QDateTime dt = QDateTime::currentDateTime();
    QString dts =   "\"" + dt.toString("yyyy-MM-dd HH:mm:ss") + "\"";

    QString script = SCRIPT_S3_SET_TIME;
    script +=  QString(" ") + dts;
    script +=  QString(" ") + zone;
    executeScript(script);
}


void AppLogic::configureNetwork(NetSettings ns) {
    QString script = SCRIPT_S4_CONFIGURE_NETWORK;

    script +=  QString(" ") + ns.hostname;
    script +=  QString(" ") + ns.iface;
    script +=  QString(" ") + ns.ip;
    script +=  QString(" ") + ns.mask;
    script +=  QString(" ") + ns.gateway;
    script +=  QString(" ") + ns.dns;
    script +=  QString(" ") + ns.vlan;

	executeScript(script);
}



void AppLogic::createInitrd() {
    QString script = SCRIPT_S5_CREATE_INITRD;
	executeScript(script);
}

void AppLogic::installBootLoader(QString device){
    QString script = SCRIPT_S6_INSTALL_BOOTLOADER;
	script +=  QString(" ") + device;
	executeScript(script);
}



void AppLogic::postInstall(){
    QString script = SCRIPT_S7_POST_INSTALL;
	executeScript(script);
}


void AppLogic::ejectDevice(QString device){
	QString script = SCRIPT_EJECT_DEVICE;
	script +=  QString(" ") + device;
	executeScript(script);
}


QVector<ZoneInfo> AppLogic::ReadZones()
{
    QVector<ZoneInfo> zones;
    QFile file(ZONE_INFO_FILE);

    if (file.open(QIODevice::ReadOnly))
    {
       QTextStream in(&file);
       while (!in.atEnd())
       {
          QString line = in.readLine().trimmed();
          if( line.startsWith("#"))
              continue;

          QStringList tokens = line.split("\t");
          if( tokens.size() < 3 )
              continue;

          ZoneInfo zi;
          zi.countryCode = tokens[0];
          zi.zone = tokens[2];
          zones.append(zi);

       }
       file.close();
    }

    return zones;
}

// upgrade support
QString AppLogic::getPrevInstallDisk()
{
    QString disk = "";
    QString script = USCRIPT_DETECT_PREV_INSTALL_DISK;
    QProcess p;
    p.start(script);

    if (p.waitForStarted(-1)) {
        while( p.waitForReadyRead(-1) )
        {
            QByteArray byteArray = p.readAllStandardOutput();
            QStringList strLines = QString(byteArray).split("\n");
            if ( 0 < strLines.size() ) {
                disk = strLines.at(0).trimmed();
            }
            break;
        }
    }

    return disk;

}

QString AppLogic::getPrevInstallVersion()
{

    QString ver = "";
    QString script = USCRIPT_DETECT_PREV_INSTALL_VERSION;
    QProcess p;
    p.start(script);

    if (p.waitForStarted(-1)) {
        while( p.waitForReadyRead(-1) )
        {
            QByteArray byteArray = p.readAllStandardOutput();
            QStringList strLines = QString(byteArray).split("\n");
            if ( 0 < strLines.size() ) {
                ver = strLines.at(0).trimmed();
            }
            break;
        }
    }

    return ver;

}

bool AppLogic::canUpgrade(QString prev_version)
{
    QString dir = USCRIPT_BASE + prev_version;
    return QDir(dir).exists();
}


void AppLogic::u_preInstall(QString device,QString prev_version)
{
    QString script = USCRIPT_BASE + prev_version + "/" + USCRIPT_U1_PRE_INSTALL;
    script +=  QString(" ") + device;
    executeScript(script);
}

void AppLogic::u_formatDisk(QString device,QString prev_version)
{
    QString script = USCRIPT_BASE + prev_version + "/" + USCRIPT_U2_FORMAT_DISK;
    script +=  QString(" ") + device;
    executeScript(script);
 }

void AppLogic::u_installRootFS(QString prev_version)
{
    QString script = USCRIPT_BASE + prev_version + "/" + USCRIPT_U3_INSTALL_ROOTFS;
    executeScript(script);
}

void AppLogic::u_createInitrd(QString prev_version)
{
    QString script = USCRIPT_BASE + prev_version + "/" + USCRIPT_U4_CREATE_INITRD;
    executeScript(script);
}

void AppLogic::u_installBootLoader(QString device,QString prev_version)
{
    QString script = USCRIPT_BASE + prev_version + "/" + USCRIPT_U5_INSTALL_BOOTLOADER;
    script +=  QString(" ") + device;
    executeScript(script);
}

void AppLogic::u_postInstall(QString prev_version)
{
    QString script = USCRIPT_BASE + prev_version + "/" + USCRIPT_U6_POST_INSTALL;
    executeScript(script);
}


