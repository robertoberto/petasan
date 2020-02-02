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

#ifndef PROGRESS_H
#define PROGRESS_H

#include <QWidget>

#include "appdata.h"
#include "applogic.h"


// progress %
#define  S1_PROGRESS_VAL  20
#define  S2_PROGRESS_VAL  80
#define  S3_PROGRESS_VAL  81
#define  S4_PROGRESS_VAL  82
#define  S5_PROGRESS_VAL  95
#define  S6_PROGRESS_VAL  97
#define  S7_PROGRESS_VAL 100

// output line counts per | wc -l
#define  S1_PROGRESS_COUNT  55
#define  S2_PROGRESS_COUNT  51000
#define  S3_PROGRESS_COUNT  1
#define  S4_PROGRESS_COUNT  1
#define  S5_PROGRESS_COUNT  1400
#define  S6_PROGRESS_COUNT  1
#define  S7_PROGRESS_COUNT  1


#define  U1_PROGRESS_VAL  3
#define  U2_PROGRESS_VAL  20
#define  U3_PROGRESS_VAL  80
#define  U4_PROGRESS_VAL  95
#define  U5_PROGRESS_VAL  97
#define  U6_PROGRESS_VAL 100

#define  U1_PROGRESS_COUNT  1
#define  U2_PROGRESS_COUNT  55
#define  U3_PROGRESS_COUNT  51000
#define  U4_PROGRESS_COUNT  1400
#define  U5_PROGRESS_COUNT  1
#define  U6_PROGRESS_COUNT  1



namespace Ui {
class ProgressForm;
}

class ProgressForm : public QWidget
{
    Q_OBJECT

public:
    AppData* data;
    AppLogic* logic;

    explicit ProgressForm(QWidget *parent,AppData* data,AppLogic* logic);
    ~ProgressForm();



protected:

	int progress_max;
	int progress_min;
	bool progress_verbose;
	int progress_out_count;
	int progress_out_count_max;
	int banner;

	void setProgressValues(int min,int max,int out_max,bool verbose);
	static bool CallBack(QString,int);
	static ProgressForm* m_pThis;
	void updateBanner(int progress);

    void install();
    void upgrade();

signals:
    void rebootEvent();


protected slots:
    void OnStart();
    void OnReboot();

private:


    void showEvent(QShowEvent * event);
    Ui::ProgressForm *ui;
};

#endif // PROGRESS_H
