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


#include <QtDebug>

#include "disksform.h"
#include "ui_disksform.h"

#include "messagebox.h"


DisksForm::DisksForm(QWidget *parent,AppData* data,AppLogic* logic) :
    QWidget(parent),
    ui(new Ui::DisksForm)
{

    this->data = data;
    this->logic = logic;

    ui->setupUi(this);

    connect(ui->nextBtn, SIGNAL( clicked()), this, SLOT( OnNext() ) );
    connect(ui->prevBtn, SIGNAL( clicked()), this, SLOT( OnPrev() ) );
    connect(ui->abortBtn, SIGNAL( clicked()), this, SLOT( OnAbort() ) );
    connect(ui->treeWidget, SIGNAL(itemSelectionChanged() ), this, SLOT( on_treeWidget_itemSelectionChanged() ) );

    connect(ui->rescanBtn, SIGNAL( clicked()), this, SLOT( on_rescanBtn_clicked() ) );

    init = false;

}


DisksForm::~DisksForm()
{
    delete ui;
}



void DisksForm::OnNext()
{
    if( !ValidateData() )
        return;

    emit nextBtnEvent();

}
void DisksForm::OnPrev()
{
    emit prevBtnEvent();

}
void DisksForm::OnAbort()
{

     emit abortBtnEvent();
}

void DisksForm::showEvent(QShowEvent * event) {


    if( !init) {
        // first time to show
        init = true;

        SetupTreeWidget();
        LoadDisks();
   }

    ui->treeWidget->setFocus();

    QTreeWidgetItem* item = ui->treeWidget->currentItem();
    if( item != NULL &&  item->isSelected() ) {
        ui->treeWidget->scrollToItem(item);
    }


    return;

}

void DisksForm::SetupTreeWidget()
{

     ui->treeWidget->setRootIsDecorated(false);
     ui->treeWidget->setSortingEnabled(false);


     QTreeWidgetItem* item = ui->treeWidget->headerItem();
     item->setText(0,"Disk");
     item->setText(1,"Size");
     item->setText(2,"Type");
     item->setText(3,"SSD");
     item->setText(4,"Model");
     item->setText(5,"Serial");

     ui->treeWidget->header()->resizeSection(0,100);
     ui->treeWidget->header()->resizeSection(1,70);
     ui->treeWidget->header()->resizeSection(2,50);
     ui->treeWidget->header()->resizeSection(3,40);
     ui->treeWidget->header()->resizeSection(4,180);
     ui->treeWidget->header()->resizeSection(5,180);


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

void DisksForm::LoadDisks() {

    QVector<DiskInfo> disks  =  logic->DetectDisks();
    for(int i=0; i < disks.size() ; i++) {
        DisplayDiskInfo(disks[i]);
    }

}

void DisksForm::DisplayDiskInfo(DiskInfo di) {
    QIcon icon;
    icon.addFile(":/icons/resources/disk1.png");
    QTreeWidgetItem* item = new QTreeWidgetItem(ui->treeWidget);
    item->setIcon(0, icon);
    item->setText(0,di.device);
    item->setText(1,di.size);
    item->setText(2,di.type);
    item->setText(3,di.ssd);
    QString s;
    if( 0 < di.vendor.length() )
        s =  di.vendor + " " + di.model;
    else
        s = di.model;
    item->setText(4,s);
    item->setText(5,di.serial);


}

void DisksForm::on_treeWidget_itemSelectionChanged()
{
    QTreeWidgetItem* item = ui->treeWidget->currentItem();
    if( item == NULL ||  !item->isSelected() ) {
        data->di.device = "";
        data->di.size = "";
        data->di.model = "";

        return;
    }

    data->di.device = item->text(0);
    data->di.size = item->text(1);
    data->di.model = item->text(4);


    qDebug() << " disk selected " << data->di.device;
}

void DisksForm::on_rescanBtn_clicked()
{
    data->di.device = "";
    data->di.size = "";
    data->di.model = "";

    ui->treeWidget->clearSelection();
    ui->treeWidget->clear();

     LoadDisks();
}

bool DisksForm::ValidateData()
{
    QTreeWidgetItem* item = ui->treeWidget->currentItem();
    if( item == NULL ||  !item->isSelected() ) {
        MessageBox::warn("No disk selected");
        return false;
    }

    // validate min disk size
    QStringList sl = item->text(1).split(" ");
    if( sl.size() != 2 ) {
        MessageBox::warn("Incorrect disk size");
        return false;

    }

    QString sizeUnit = sl[1];  // in T or G
    if( sizeUnit.compare( "G",Qt::CaseInsensitive) == 0 ) {
         int sizeGigs = sl[0].toInt();
         if( sizeGigs < MIN_DISK_SIZE_GIGS ) {
             QString message = "A disk with a capacity of ";
             message += QString::number(MIN_DISK_SIZE_GIGS);
             message += " G or more is required";

             MessageBox::warn(message);
             return false;
         }
    }

    if( !data->prev_install_disk.isEmpty() ) {

        QString d = "/dev/" + data->di.device;
        if( d.compare( data->prev_install_disk,Qt::CaseInsensitive) != 0 ) {
            QString message = "A previous installation exists on disk: ";
            message += data->prev_install_disk;
            message += ". Are you sure you wish to install on another disk ?";

            if ( !MessageBox::confirm(message) )
                return false;

        }

    }



    return true;
}
