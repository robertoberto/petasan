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

#include <QFontDialog>

#include "ipvalidator.h"
#include "messagebox.h"

#include "networkform.h"
#include "ui_networkform.h"

NetworkForm::NetworkForm(QWidget *parent,AppData* data,AppLogic* logic) :
    QWidget(parent),
    ui(new Ui::NetworkForm)
{

    this->data = data;
    this->logic = logic;


    ui->setupUi(this);

    connect(ui->nextBtn, SIGNAL( clicked()), this, SLOT( OnNext() ) );
    connect(ui->prevBtn, SIGNAL( clicked()), this, SLOT( OnPrev() ) );
    connect(ui->abortBtn, SIGNAL( clicked()), this, SLOT( OnAbort() ) );

    //connect(ui->pushButton, SIGNAL( clicked()), this, SLOT( on_pushButton_clicked() ) );

    connect(ui->vlanCheckBox, SIGNAL( clicked()), this, SLOT( on_vlanCheckBox_clicked() ) );

    /*
    ui->vlan->setEnabled(false);
    QPalette palette = ui->vlan->palette();
    palette.setColor(QPalette::Disabled,QPalette::Text, QColor(64,64,64));
    palette.setColor(QPalette::Disabled,QPalette::Base, QColor(192,192,192));
    ui->vlan->setPalette(palette);
    */

    ui->vlan->setHidden(true);


    init = false;


}


NetworkForm::~NetworkForm()
{
    delete ui;
}

void NetworkForm::OnNext()
{
    if( !ValidateData() )
        return;

    QTreeWidgetItem* item = ui->treeWidget->currentItem();
    data->ns.iface = item->text(0);

    data->ns.hostname = ui->hostname->text();
    data->ns.ip = ui->ip->text();
    data->ns.mask = ui->mask->text();
    data->ns.gateway = ui->gateway->text();
    data->ns.dns = ui->dns->text();

    if( ui->vlanCheckBox->isChecked() )
        data->ns.vlan = ui->vlan->text();
    else
        data->ns.vlan = "";


    emit nextBtnEvent();
}


void NetworkForm::OnPrev()
{
    emit prevBtnEvent();

}
void NetworkForm::OnAbort()
{
    //OnDebugFonts();
    emit abortBtnEvent();
}

void NetworkForm::showEvent(QShowEvent * event) {

    if( !init) {
        // first time to show
        init = true;

        SetupTreeWidget();
        LoadIFs();

        // default values
        //ui->hostname->setText("ps-node-01");
        ui->mask->setText( "255.255.255.0" );
        ui->dns->setText("8.8.8.8");
        ui->vlan->setText("1");
   }

    QTreeWidgetItem* item = ui->treeWidget->currentItem();
    if( item == NULL ||  !item->isSelected() ) {
        ui->hostname->setFocus();
        ui->hostname->selectAll();
    } else {
        ui->treeWidget->setFocus();
        ui->treeWidget->scrollToItem(item);
    }

    return;

}




void NetworkForm::SetupTreeWidget()
{

     ui->treeWidget->setRootIsDecorated(false);
     ui->treeWidget->setSortingEnabled(false);


     QTreeWidgetItem* item = ui->treeWidget->headerItem();
     item->setText(0,"Interface");
     item->setText(1,"MAC Address");
     item->setText(2,"Model");


     ui->treeWidget->header()->resizeSection(0,80);
     ui->treeWidget->header()->resizeSection(1,150);
     ui->treeWidget->header()->resizeSection(2,700);



 #if QT_VERSION >= 0x050000
     // Qt5
     //ui->treeWidget->header()->setSectionResizeMode(QHeaderView::Fixed);
     ui->treeWidget->header()->setSectionsMovable(false); // Qt5

 #else
     // Qt4
     //ui->treeWidget->header()->setResizeMode(QHeaderView::Fixed);
     ui->treeWidget->header()->setMovable(false); // Qt4
 #endif

}

void NetworkForm::LoadIFs() {

    QVector<IFInfo> ifs  =  logic->DetectInterfaces();
    for(int i=0; i < ifs.size() ; i++) {
        DisplayIFInfo(ifs[i]);
    }

    //IFInfo ifi = IFInfo("eth0","22","nac","Intel Gigabit");
    //DisplayIFInfo(ifi);

}

void NetworkForm::DisplayIFInfo(IFInfo ifi) {
    QIcon icon;
    icon.addFile(":/icons/resources/if1.png");
    QTreeWidgetItem* item = new QTreeWidgetItem(ui->treeWidget);
    item->setIcon(0, icon);
    item->setText(0,ifi.iface);
    item->setText(1,ifi.mac);
    item->setText(2,ifi.model);

}

void NetworkForm::on_vlanCheckBox_clicked()
{
    if( ui->vlanCheckBox->isChecked() )
        ui->vlan->setHidden(false);
    else
        ui->vlan->setHidden(true);
}

void NetworkForm::OnDebugFonts()
{
    bool ok;
    QFont font = QFontDialog::getFont(&ok, QFont("Sans Serif", 11), this);
    if (ok) {
        qApp->setFont(font);

    }
}


bool NetworkForm::ValidateData()
{
    if( !ValidateHostname() ) {
        MessageBox::warn("Invalid Hostname");
        ui->hostname->setFocus();
        ui->hostname->selectAll();
        return false;
    }


    QTreeWidgetItem* item = ui->treeWidget->currentItem();
    if( item == NULL ||  !item->isSelected() ) {
        MessageBox::warn("No Interface selected");
        return false;
    }


    if( !ValidateIp() ) {
        MessageBox::warn("Invalid IP Address");
        ui->ip->setFocus();
        ui->ip->selectAll();
        return false;
    }

    if( !ValidateMask() ) {
        MessageBox::warn("Invalid Subnet Mask");
        ui->mask->setFocus();
        ui->mask->selectAll();
        return false;
    }

    if( !ValidateGateway() ) {
        MessageBox::warn("Invalid Gateway Address");
        ui->gateway->setFocus();
        ui->gateway->selectAll();
        return false;
    }

    if( !ValidateDNS() ) {
        MessageBox::warn("Invalid DNS Address");
        ui->dns->setFocus();
        ui->dns->selectAll();
        return false;
    }

    if( !ValidateVLAN() ) {
        MessageBox::warn("Invalid VLAN");
        ui->vlan->setFocus();
        ui->vlan->selectAll();
        return false;
    }


    return true;
}

bool NetworkForm::ValidateHostname()
{
    if( ui->hostname->text().length() == 0 )
        return false;

    if( ui->hostname->text().contains(".") )
        return false;

    return true;
}

bool NetworkForm::ValidateIp()
{
    return IpValidator::validateIp(ui->ip->text());
}

bool NetworkForm::ValidateMask()
{
   return IpValidator::validateMask(ui->mask->text());
}

bool NetworkForm::ValidateGateway()
{
    return IpValidator::validateIp(ui->gateway->text());
}

bool NetworkForm::ValidateDNS()
{
    return IpValidator::validateIp(ui->dns->text());
}


bool NetworkForm::ValidateVLAN()
{
    if( !ui->vlanCheckBox->isChecked() )
        return true;

    if( ui->vlan->text().length() == 0 )
        return false;

    bool ok;
    int id =  ui->vlan->text().toInt(&ok);
    if( !ok )
        return false;
    if( id < 1 || 4095 < id )
        return false;
    return true;
}




