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

#include <QDesktopWidget>

#include "mainwindow.h"
#include "ui_mainwindow.h"



#include "licenseform.h"
#include "networkform.h"
#include "disksform.h"
#include "confirmform.h"
#include "progressform.h"
#include "clockform.h"
#include "upgradeform.h"


MainWindow::MainWindow(QWidget *parent,AppData* datax,AppLogic* logicx) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    this->data = datax;
    this->logic = logicx;

    widgetIndex = 0;

    QWidget* licenseForm = new LicenseForm();
    ui->stackedWidget->addWidget(licenseForm);
    connect(licenseForm, SIGNAL( nextBtnEvent()), this, SLOT( OnNext() ) );
    connect(licenseForm, SIGNAL( abortBtnEvent()), this, SLOT( OnAbort() ) );

    if( !data->prev_install_version.isEmpty() ) {
        // add upgrade form
        QWidget* upgradeForm = new UpgradeForm(0,data,logic);
        ui->stackedWidget->addWidget(upgradeForm);
        connect(upgradeForm, SIGNAL( nextBtnEvent()), this, SLOT( OnNext() ) );
        connect(upgradeForm, SIGNAL( prevBtnEvent()), this, SLOT( OnPrev() ) );
        connect(upgradeForm, SIGNAL( abortBtnEvent()), this, SLOT( OnAbort() ) );
    }

    QWidget* networkForm = new NetworkForm(0,data,logic);
    ui->stackedWidget->addWidget(networkForm);
    connect(networkForm, SIGNAL( nextBtnEvent()), this, SLOT( OnNext() ) );
    connect(networkForm, SIGNAL( prevBtnEvent()), this, SLOT( OnPrev() ) );
    connect(networkForm, SIGNAL( abortBtnEvent()), this, SLOT( OnAbort() ) );

    QWidget* disksForm = new DisksForm(0,data,logic);
    ui->stackedWidget->addWidget(disksForm);
    connect(disksForm, SIGNAL( nextBtnEvent()), this, SLOT( OnNext() ) );
    connect(disksForm, SIGNAL( prevBtnEvent()), this, SLOT( OnPrev() ) );
    connect(disksForm, SIGNAL( abortBtnEvent()), this, SLOT( OnAbort() ) );

    QWidget* clockForm = new ClockForm(0,data,logic);
    ui->stackedWidget->addWidget(clockForm);
    connect(clockForm, SIGNAL( nextBtnEvent()), this, SLOT( OnNext() ) );
    connect(clockForm, SIGNAL( prevBtnEvent()), this, SLOT( OnPrev() ) );
    connect(clockForm, SIGNAL( abortBtnEvent()), this, SLOT( OnAbort() ) );

    QWidget* confirmForm = new ConfirmForm(0,data,logic);
    ui->stackedWidget->addWidget(confirmForm);
    connect(confirmForm, SIGNAL( nextBtnEvent()), this, SLOT( OnNext() ) );
    connect(confirmForm, SIGNAL( prevBtnEvent()), this, SLOT( OnPrev() ) );
    connect(confirmForm, SIGNAL( abortBtnEvent()), this, SLOT( OnAbort() ) );


    QWidget* progressWidget = new ProgressForm(0,data,logic);
    ui->stackedWidget->addWidget(progressWidget);

    PlaceWindow();
}

MainWindow::~MainWindow()
{
    delete ui;
}


void MainWindow::OnAbort()
{

    qApp->exit();
}

void MainWindow::OnNext()
{
    if( widgetIndex == 1 && !data->new_install )
        widgetIndex = 6;
    else
        widgetIndex++;

    ui->stackedWidget->setCurrentIndex(widgetIndex);

}

void MainWindow::OnPrev()
{

    widgetIndex--;
    ui->stackedWidget->setCurrentIndex(widgetIndex);
}

void MainWindow::PlaceWindow()
{
    setWindowFlags(Qt::FramelessWindowHint);
    resize(WINDOW_WIDTH,WINDOW_HEIGHT);
    setFixedSize(WINDOW_WIDTH,WINDOW_HEIGHT);

    QRect rect = QApplication::desktop()->availableGeometry();
    move( rect.center() - this->rect().center() );
}

