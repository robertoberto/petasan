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
#include <QTimer>

#include <unistd.h>


#include "progressform.h"
#include "ui_progressform.h"
#include "messagebox.h"
#include <math.h>



ProgressForm* ProgressForm::m_pThis = NULL;


ProgressForm::ProgressForm(QWidget *parent,AppData* data,AppLogic* logic) :
    QWidget(parent),
    ui(new Ui::ProgressForm)
{
	m_pThis = this;
    this->data = data;
    this->logic = logic;


    ui->setupUi(this);

    connect(ui->rebootBtn, SIGNAL( clicked()), this, SLOT( OnReboot() ) );

	 this->logic->setCallBack(CallBack);

/*
    this->logic->setConsole(ui->statusCtrl);

    ui->statusCtrl->setTextColor( QColor(0,255,0) ) ;
    //ui->statusCtrl->setTextBackgroundColor(QColor(0,0,0));

    QPalette palette;
    QBrush brush(QColor(35, 35, 35));
    brush.setStyle(Qt::SolidPattern);
    palette.setBrush(QPalette::Active, QPalette::Base, brush);

    //palette.setBrush(QPalette::Inactive, QPalette::Base, brush);
    //QBrush brush1(QColor(255, 255, 255, 255));
    //brush1.setStyle(Qt::SolidPattern);
    //palette.setBrush(QPalette::Disabled, QPalette::Base, brush1);

    ui->statusCtrl->setPalette(palette);
    QFont font("Courier",9  );
    //ui->statusCtrl->setFont( font );
*/
}

ProgressForm::~ProgressForm()
{
    delete ui;
}

void ProgressForm::showEvent(QShowEvent * event) {
    QTimer *timer = new QTimer(this);
    timer->setSingleShot(true);
    connect(timer, SIGNAL(timeout()), this, SLOT(OnStart()));
    timer->start(100);
}

void ProgressForm::OnReboot()
{

	QString installDevice = logic->getInstallDevice();
	if( installDevice !=NULL && !installDevice.isEmpty() ) {
		if( installDevice.startsWith("/dev/sd",Qt::CaseInsensitive) ) {
			// USB install device plugged in
			QString msg = "Please remove installation device.\n";
			msg += "Failure to remove it now may result in incorrect system behaviour";
			MessageBox::warn(msg);
			return;
		}
	}

    //logic->executeScript("reboot");
    qApp->exit();
}


void ProgressForm::setProgressValues(int min,int max,int out_max,bool verbose) {

	progress_out_count = 0;
	progress_min = min;
	progress_max = max;
	progress_out_count_max = out_max;
	progress_verbose = verbose;
	ui->progressCtrl->setValue(progress_min);
}



void  ProgressForm::OnStart() {

    QString installDevice = logic->getInstallDevice();
    bool isCDInstall = false;

    if( installDevice !=NULL && !installDevice.isEmpty() ) {
        if( installDevice.startsWith("/dev/sr",Qt::CaseInsensitive) ) {
            isCDInstall = true;
        }
    }

    banner = 1;
    ui->rebootBtn->setEnabled(false);

    if( data->new_install )
        install();
    else
        upgrade();


    if( isCDInstall ) {
        ui->progressLabel->setText("Ejecting CD device");
        logic->ejectDevice(installDevice);
    }

    ui->progressLabel->setText("Installation complete. Please reboot your system");
    ui->rebootBtn->setEnabled(true);
    ui->imagesLabel->setPixmap(QPixmap(":/images/resources/b6.png"));

}

void  ProgressForm::upgrade() {

    ui->progressLabel->setText("Performing pre install");
    setProgressValues(0,U1_PROGRESS_VAL,U1_PROGRESS_COUNT,true);
    logic->u_preInstall(data->prev_install_disk,data->prev_install_version);

    ui->progressLabel->setText("Partitioning and Formatting disk");
    setProgressValues(U1_PROGRESS_VAL,U2_PROGRESS_VAL,U2_PROGRESS_COUNT,true);
    logic->u_formatDisk(data->prev_install_disk,data->prev_install_version);

    ui->progressLabel->setText("Installing PetaSAN root filesystem");
    setProgressValues(U2_PROGRESS_VAL,U3_PROGRESS_VAL,U3_PROGRESS_COUNT,true);
    logic->u_installRootFS(data->prev_install_version);

    ui->progressLabel->setText("Creating initial RAM disk");
    setProgressValues(U3_PROGRESS_VAL,U4_PROGRESS_VAL,U4_PROGRESS_COUNT,true);
    logic->u_createInitrd(data->prev_install_version);

    ui->progressLabel->setText("Installing boot loader");
    setProgressValues(U4_PROGRESS_VAL,U5_PROGRESS_VAL,U5_PROGRESS_COUNT,true);
    logic->u_installBootLoader(data->prev_install_disk,data->prev_install_version);

    ui->progressCtrl->setValue(100);
    this->logic->setCallBack(NULL);
    ui->progressLabel->setText("Performing post install");
    this->logic->u_postInstall(data->prev_install_version);

}

void  ProgressForm::install() {

    ui->progressLabel->setText("Partitioning and Formatting disk");
    setProgressValues(0,S1_PROGRESS_VAL,S1_PROGRESS_COUNT,true);
    logic->formatDisk("/dev/" + data->di.device);

    ui->progressLabel->setText("Installing PetaSAN root filesystem");
    setProgressValues(S1_PROGRESS_VAL,S2_PROGRESS_VAL,S2_PROGRESS_COUNT,true);
    logic->installRootFS();

    ui->progressLabel->setText("Setting Date & Time");
    setProgressValues(S2_PROGRESS_VAL,S3_PROGRESS_VAL,S3_PROGRESS_COUNT,true);
    logic->setTime(data->zone);

    ui->progressLabel->setText("Configuring network");
    setProgressValues(S3_PROGRESS_VAL,S4_PROGRESS_VAL,S4_PROGRESS_COUNT,true);
    logic->configureNetwork(data->ns);

    ui->progressLabel->setText("Creating initial RAM disk");
    setProgressValues(S4_PROGRESS_VAL,S5_PROGRESS_VAL,S5_PROGRESS_COUNT,true);
    logic->createInitrd();

    ui->progressLabel->setText("Installing boot loader");
    setProgressValues(S5_PROGRESS_VAL,S6_PROGRESS_VAL,S6_PROGRESS_COUNT,true);
    logic->installBootLoader("/dev/" +data->di.device);

    ui->progressCtrl->setValue(100);
    this->logic->setCallBack(NULL);
    ui->progressLabel->setText("Performing post install");
    this->logic->postInstall();


}

bool ProgressForm::CallBack(QString,int) {

	m_pThis->progress_out_count++;

	float range = m_pThis->progress_max - m_pThis->progress_min;
	float fraction = ((float)m_pThis->progress_out_count ) / ((float)m_pThis->progress_out_count_max );
	if( 1.0 < fraction )
		fraction = 1.0;
	float progress = m_pThis->progress_min + range * fraction;

	if( m_pThis->ui->progressCtrl->value() < floor(progress) )
		m_pThis->ui->progressCtrl->setValue(progress);

	m_pThis->updateBanner(progress);

	if( m_pThis->progress_verbose ) {

		/*
		m_pThis->ui->ui->statusCtrl->insertPlainText(QString(buff) );
		QScrollBar *sb = m_pThis->ui->ui->statusCtrl->verticalScrollBar();
		sb->setValue(sb->maximum());
		*/
	}
	qApp->processEvents();
	return true;
}



void ProgressForm::updateBanner(int progress) {
	if( 80 < progress ) {
		if( banner != 5 ) {
			banner = 5;
			ui->imagesLabel->setPixmap(QPixmap(":/images/resources/b5.png"));
		}
		return;
	}

	if( 60 < progress ) {
		if( banner != 4 ) {
			banner = 4;
			ui->imagesLabel->setPixmap(QPixmap(":/images/resources/b4.png"));
		}
		return;
	}

	if( 40 < progress ) {
		if( banner != 3 ) {
			banner = 3;
			ui->imagesLabel->setPixmap(QPixmap(":/images/resources/b3.png"));
		}
		return;
	}

	if( 17 < progress ) {
		if( banner != 2 ) {
			banner = 2;
			ui->imagesLabel->setPixmap(QPixmap(":/images/resources/b2.png"));
		}
		return;
	}

}

