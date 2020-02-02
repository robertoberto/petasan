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

#ifndef LICENSE_H
#define LICENSE_H

#include <QWidget>

namespace Ui {
class LicenseForm;
}

class LicenseForm : public QWidget
{
    Q_OBJECT

public:
    explicit LicenseForm(QWidget *parent = 0);
    ~LicenseForm();

signals:
    void nextBtnEvent();
    void abortBtnEvent();

protected slots:
    void OnNext();
    void OnAbort();

private slots:


    void on_agreeCkeckBox_clicked();

private:
    Ui::LicenseForm *ui;
};

#endif // LICENSE_H
