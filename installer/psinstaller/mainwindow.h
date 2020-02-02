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

#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

#include <QVector>

#include "appdata.h"
#include "applogic.h"

#define WINDOW_WIDTH 760
#define WINDOW_HEIGHT 350



namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:

    AppData* data;
    AppLogic* logic;

    explicit MainWindow(QWidget *parent,AppData* data,AppLogic* logic);
    ~MainWindow();

private:
    Ui::MainWindow *ui;
    int widgetIndex;
    //QVector<QWidget> panes;

protected:
    void PlaceWindow();

protected slots:
    void OnAbort();
    void OnNext();
    void OnPrev();
};

#endif // MAINWINDOW_H
