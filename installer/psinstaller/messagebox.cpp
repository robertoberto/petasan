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


#include <QApplication>
#include <QDesktopWidget>
#include <Qt>

#include "messagebox.h"


void MessageBox::warn(QString message)
{

    QMessageBox mb(QMessageBox::Warning,NULL,message,
//                   QMessageBox::Ok,NULL, Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint);
    QMessageBox::Ok,NULL);
     show(&mb);
    mb.exec();
}

bool MessageBox::confirm(QString message)
{
    QMessageBox mb(QMessageBox::Warning,NULL,message,
             QMessageBox::Yes | QMessageBox::No,NULL, Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint);
    show(&mb);
    int ret = mb.exec();
    if( ret == QMessageBox::Yes )
        return true;
    return false;

}

void MessageBox::show(QWidget* w)
{
    Qt::WindowFlags flags =0;
    //flags = Qt::CustomizeWindowHint;
    //flags = Qt::FramelessWindowHint;
    flags = Qt::WindowTitleHint;
	w->setWindowTitle(" ");
    w->setWindowFlags(flags);
    //w->setFixedSize(250, 100);
    w->show();
    QRect rect = QApplication::desktop()->availableGeometry();
    w->move( rect.center() - w->rect().center() );

}
