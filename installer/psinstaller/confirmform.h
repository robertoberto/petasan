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

#ifndef CONFIRMFORM_H
#define CONFIRMFORM_H

#include <QWidget>
#include "appdata.h"
#include "applogic.h"

namespace Ui {
class ConfirmForm;
}

class ConfirmForm : public QWidget
{
    Q_OBJECT


public:
    AppData* data;
    AppLogic* logic;

    explicit ConfirmForm(QWidget *parent,AppData* data,AppLogic* logic);
    ~ConfirmForm();

signals:
    void nextBtnEvent();
    void prevBtnEvent();
    void abortBtnEvent();

protected slots:
    void OnNext();
    void OnPrev();
    void OnAbort();

protected:
bool ConfirmInstall();


private:
    void showEvent(QShowEvent * event);
    Ui::ConfirmForm *ui;
};

#endif // CONFIRMFORM_H
