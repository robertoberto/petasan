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

#ifndef NETWORK_H
#define NETWORK_H

#include <QWidget>

#include "appdata.h"
#include "applogic.h"
#include "ifinfo.h"

namespace Ui {
class NetworkForm;
}

class NetworkForm : public QWidget
{
    Q_OBJECT

public:
    AppData* data;
    AppLogic* logic;

    explicit NetworkForm(QWidget *parent,AppData* data,AppLogic* logic);
    ~NetworkForm();

signals:
    void nextBtnEvent();
    void prevBtnEvent();
    void abortBtnEvent();

protected slots:
    void OnNext();
    void OnPrev();
    void OnAbort();
    void on_vlanCheckBox_clicked();

protected:
    bool init;
    void SetupTreeWidget();
    void LoadIFs();
    void DisplayIFInfo(IFInfo ifi);
    bool ValidateData();
    bool ValidateHostname();
    bool ValidateIp();
    bool ValidateMask();
    bool ValidateGateway();
    bool ValidateDNS();
    bool ValidateVLAN();



private slots:
    void OnDebugFonts();

private:
    void showEvent(QShowEvent * event);
    Ui::NetworkForm *ui;
};

#endif // NETWORK_H
