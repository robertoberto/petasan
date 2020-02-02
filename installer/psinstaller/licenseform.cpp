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

#include "licenseform.h"
#include "ui_licenseform.h"

LicenseForm::LicenseForm(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::LicenseForm)
{
    ui->setupUi(this);

    connect(ui->abortBtn, SIGNAL( clicked()), this, SLOT( OnAbort() ) );
    connect(ui->nextBtn, SIGNAL( clicked()), this, SLOT( OnNext() ) );
    connect(ui->agreeCkeckBox, SIGNAL( clicked()), this, SLOT( on_agreeCkeckBox_clicked() ) );

    ui->nextBtn->setEnabled(false);
    ui->prevBtn->setEnabled(false);
}

LicenseForm::~LicenseForm()
{
    delete ui;
}


void LicenseForm::OnAbort()
{

     emit abortBtnEvent();
}

void LicenseForm::OnNext()
{
    emit nextBtnEvent();

}

void LicenseForm::on_agreeCkeckBox_clicked()
{
    if( ui->agreeCkeckBox->isChecked() )
        ui->nextBtn->setEnabled(true);
    else
         ui->nextBtn->setEnabled(false);
}
