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

#ifndef DISKS_H
#define DISKS_H

#include <QWidget>

#include "appdata.h"
#include "applogic.h"

#include "diskinfo.h"

namespace Ui {
class DisksForm;
}



class DisksForm : public QWidget
{
    Q_OBJECT

public:

    AppData* data;
    AppLogic* logic;

    explicit DisksForm(QWidget *parent,AppData* data,AppLogic* logic);
    ~DisksForm();

signals:
    void nextBtnEvent();
    void prevBtnEvent();
    void abortBtnEvent();

protected slots:
    void OnNext();
    void OnPrev();
    void OnAbort();

protected:
    bool init;
    void SetupTreeWidget();
    void LoadDisks();
    void DisplayDiskInfo(DiskInfo di);
    bool ValidateData();


private slots:
    void on_treeWidget_itemSelectionChanged();



    void on_rescanBtn_clicked();

private:
    void showEvent(QShowEvent * event);
    Ui::DisksForm *ui;
};

#endif // DISKS_H


