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

#include "confirmform.h"
#include "ui_confirmform.h"

#include "messagebox.h"



ConfirmForm::ConfirmForm(QWidget *parent,AppData* data,AppLogic* logic) :
    QWidget(parent),
    ui(new Ui::ConfirmForm)
{
    this->data = data;
    this->logic = logic;

    ui->setupUi(this);

    connect(ui->nextBtn, SIGNAL( clicked()), this, SLOT( OnNext() ) );
    connect(ui->prevBtn, SIGNAL( clicked()), this, SLOT( OnPrev() ) );
    connect(ui->abortBtn, SIGNAL( clicked()), this, SLOT( OnAbort() ) );



}

ConfirmForm::~ConfirmForm()
{
    delete ui;
}


void ConfirmForm::OnNext()
{
    if( !ConfirmInstall() )
        return;

    emit nextBtnEvent();

}
void ConfirmForm::OnPrev()
{
    emit prevBtnEvent();

}
void ConfirmForm::OnAbort()
{

     emit abortBtnEvent();
}

void ConfirmForm::showEvent(QShowEvent * event)
{
    QString s;

    ui->summaryCtrl->clear();

    //s = "<p align='center' style='color:#000080; font-size:15pt; font-weight:bold'>Installation Summary</p>";
    //ui->summaryCtrl->append(s);

    s = "<br>";
    ui->summaryCtrl->insertHtml(s);

    s = "<b> <font color=\"#000080\">Installation Disk</font> </b> <br>";
    ui->summaryCtrl->insertHtml(s);
    s = "Disk device: /dev/" + data->di.device + "<br>";
    ui->summaryCtrl->insertHtml(s);
    s = "Size: " + data->di.size + "<br>";
    ui->summaryCtrl->insertHtml(s);
    s = "Model: " + data->di.model + "<br>";
    ui->summaryCtrl->insertHtml(s);

    s = "<br>";
    ui->summaryCtrl->insertHtml(s);

    s = "<b> <font color=\"#000080\">Network Configuration</font> </b> <br>";
    ui->summaryCtrl->insertHtml(s);
    s = "Hostname: " + data->ns.hostname + "<br>";
    ui->summaryCtrl->insertHtml(s);

    s = "Management Interface: " + data->ns.iface + "<br>";
    ui->summaryCtrl->insertHtml(s);


    s = "IP Address: " + data->ns.ip + "<br>";
    ui->summaryCtrl->insertHtml(s);
    s = "Mask: " + data->ns.mask + "<br>";
    ui->summaryCtrl->insertHtml(s);
    if( 0 <  data->ns.vlan.length() ) {
        s = "VLAN: " + data->ns.vlan + "<br>";
        ui->summaryCtrl->insertHtml(s);
    }

    s = "Gateway: " + data->ns.gateway + "<br>";
    ui->summaryCtrl->insertHtml(s);
    s = "DNS: " + data->ns.dns + "<br>";
    ui->summaryCtrl->insertHtml(s);

    s = "<br>";
    ui->summaryCtrl->insertHtml(s);

    s = "<b> <font color=\"#000080\">Time Setup</font> </b> <br>";
    ui->summaryCtrl->insertHtml(s);
    s = "Zone: " + data->zone + "<br>";
    ui->summaryCtrl->insertHtml(s);

    return;
}

bool ConfirmForm::ConfirmInstall()
{
    return MessageBox::confirm("All data on selected disk will be erased.\nContinue with installation?");

}

