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

#include "upgradeform.h"
#include "ui_upgradeform.h"

#include "messagebox.h"

UpgradeForm::UpgradeForm(QWidget *parent,AppData* data,AppLogic* logic) :
    QWidget(parent),
    ui(new Ui::UpgradeForm)
{


    this->data = data;
    this->logic = logic;

    ui->setupUi(this);

    connect(ui->nextBtn, SIGNAL( clicked()), this, SLOT( OnNext() ) );
    connect(ui->prevBtn, SIGNAL( clicked()), this, SLOT( OnPrev() ) );
    connect(ui->abortBtn, SIGNAL( clicked()), this, SLOT( OnAbort() ) );


    QString message;
    message += "<html>";
    message += "A previous installation of PetaSAN version <b>";
    message += data->prev_install_version;
    message += "</b> was detected on disk <b>";
    message += data->prev_install_disk;
    message += "</b>.</html>";

   ui->infoLabel->setWordWrap(true);
   ui->infoLabel->setText(message);

   if( data->can_upgrade  ) {

       ui->upgradeBtn->setChecked(true);
       ui->newBtn->setChecked(false);
   }
   else {

       ui->upgradeBtn->setChecked(false);
       ui->upgradeBtn->setEnabled(false);
       ui->upgradeLabel->setEnabled(false);
       ui->newBtn->setChecked(true);
   }

}


UpgradeForm::~UpgradeForm()
{
    delete ui;
}


void UpgradeForm::OnNext()
{
    QString mess = "Proceed with Upgrade ?";

    if ( !ui->newBtn->isChecked() && !MessageBox::confirm(mess) )
         return;

    data->new_install =  ui->newBtn->isChecked();
    emit nextBtnEvent();
}

void UpgradeForm::OnPrev()
{
    emit prevBtnEvent();
}

void UpgradeForm::OnAbort()
{
     emit abortBtnEvent();
}
