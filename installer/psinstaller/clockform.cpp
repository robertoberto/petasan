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

#include <QTimer>
#include <QProcess>
#include <QtDebug>

#include "messagebox.h"
#include "clockform.h"
#include "ui_clockform.h"


ClockForm::ClockForm(QWidget *parent,AppData* data,AppLogic* logic) :
    QWidget(parent),
    ui(new Ui::ClockForm)
{


    this->data = data;
    this->logic = logic;

    ui->setupUi(this);



    connect(ui->nextBtn, SIGNAL( clicked()), this, SLOT( OnNext() ) );
    connect(ui->prevBtn, SIGNAL( clicked()), this, SLOT( OnPrev() ) );
    connect(ui->abortBtn, SIGNAL( clicked()), this, SLOT( OnAbort() ) );



    QPalette palette = ui->dateTimeEdit->palette();
    palette.setColor(QPalette::Disabled,QPalette::Text, QColor(64,64,64));
    ui->dateTimeEdit->setPalette(palette);

    //ui->dateTimeEdit->setMinimumDate(QDate::currentDate().addDays(-365));
    //ui->dateTimeEdit->setMaximumDate(QDate::currentDate().addDays(365));
    ui->dateTimeEdit->setCalendarPopup(true);

    timer = new QTimer(this);
    connect(timer, SIGNAL(timeout()), this, SLOT(OnTimer()));


    init = false;

    connect(ui->editClock, SIGNAL( clicked()), this, SLOT( OnEditClockClicked() ) );
    connect(ui->dateTimeEdit, SIGNAL( dateTimeChanged(const QDateTime &)), this, SLOT( OnClockChanged() ) );

    connect(ui->treeWidget, SIGNAL(itemSelectionChanged() ), this, SLOT( on_treeWidget_itemSelectionChanged() ) );


}

ClockForm::~ClockForm()
{
    delete ui;
}


void ClockForm::OnNext()
{

    QTreeWidgetItem* item = ui->treeWidget->currentItem();
    if( item == NULL ||  !item->isSelected() ) {
        MessageBox::warn("No Zone selected");
        return;
    }

    StopClockDisplay();
    emit nextBtnEvent();
}


void ClockForm::OnPrev()
{
    StopClockDisplay();
    emit prevBtnEvent();

}

void ClockForm::OnAbort()
{
     emit abortBtnEvent();
}

void ClockForm::showEvent(QShowEvent * event) {

    if( ! init ) {
        init = true;
        SetupTreeWidget();
        LoadZones();
    }

    ui->treeWidget->setFocus();
    QTreeWidgetItem* item = ui->treeWidget->currentItem();
    if( item != NULL &&  item->isSelected() )
        ui->treeWidget->scrollToItem(item);

    StartClockDisplay();
}

void ClockForm::OnTimer()
{
    ui->dateTimeEdit->setDateTime(QDateTime::currentDateTime());

}

void ClockForm::OnEditClockClicked()
{
    if( ui->editClock->isChecked() ) {
        StartClockEdit();
        return;
    }

    StopClockEdit();

}



void ClockForm::StartClockDisplay()
{
    ui->dateTimeEdit->setEnabled(false);
    ui->dateTimeEdit->setDisplayFormat("hh:mm:ss AP  MMM d, yyyy");
    ui->dateTimeEdit->setDateTime(QDateTime::currentDateTime());
    timer->start(500);

}

void ClockForm::StopClockDisplay()
{
    timer->stop();
}

void ClockForm::StartClockEdit()
{

    ui->prevBtn->setEnabled(false);
    ui->nextBtn->setEnabled(false);
    ui->treeWidget->setEnabled(false);

    this->clockChanged = false;
    timer->stop();
    ui->dateTimeEdit->setEnabled(true);

    ui->dateTimeEdit->setDisplayFormat("hh:mm AP  MMM d, yyyy");
    ui->dateTimeEdit->setFocus();

}

void ClockForm::StopClockEdit()
{

    ui->prevBtn->setEnabled(true);
    ui->nextBtn->setEnabled(true);
    ui->treeWidget->setEnabled(true);

    if( this->clockChanged ) {
        this->setCursor(Qt::WaitCursor);
        QDateTime dt = ui->dateTimeEdit->dateTime();
        QString cmd;
        cmd = "date -s  ";

        cmd += "\"" + dt.toString("yyyy-MM-dd HH:mm") + "\"";
        qDebug() << " setting date command " << cmd;
        this->logic->executeScript(cmd);
        this->setCursor(Qt::ArrowCursor);
    }

    ui->treeWidget->setFocus();
    QTreeWidgetItem* item = ui->treeWidget->currentItem();
    if( item != NULL &&  item->isSelected() )
        ui->treeWidget->scrollToItem(item);

    StartClockDisplay();

}

void ClockForm::OnClockChanged()
{
    this->clockChanged = true;
}

void ClockForm::SetupTreeWidget()
{
    ui->treeWidget->setRootIsDecorated(false);
    ui->treeWidget->setSortingEnabled(false);


    QTreeWidgetItem* item = ui->treeWidget->headerItem();
    item->setText(0,"Country Code");
    item->setText(1,"Zone");

    ui->treeWidget->header()->resizeSection(0,130);
    //ui->treeWidget->header()->resizeSection(1,170);



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

void ClockForm::LoadZones()
{

    QVector<ZoneInfo> zones  =  logic->ReadZones();
    for(int i=0; i < zones.size() ; i++) {

        QTreeWidgetItem* item = new QTreeWidgetItem(ui->treeWidget);
        item->setText(0,zones[i].countryCode);
        item->setText(1,zones[i].zone);

    }
}



void ClockForm::on_treeWidget_itemSelectionChanged()
{
    QTreeWidgetItem* item = ui->treeWidget->currentItem();
    if( item == NULL ||  !item->isSelected() ) {
        data->zone = "";
        return;
    }

    data->zone = item->text(1);

    qDebug() << " zone selected " << data->zone;
}




