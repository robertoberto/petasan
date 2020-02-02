#-------------------------------------------------
#
# Project created by QtCreator 2015-12-29T15:19:37
#
#-------------------------------------------------

QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = psinstaller
TEMPLATE = app


SOURCES += main.cpp\
    mainwindow.cpp \
    disksform.cpp \
    licenseform.cpp \
    networkform.cpp \
    progressform.cpp \
    applogic.cpp \
    appdata.cpp \
    confirmform.cpp \
    messagebox.cpp \
    ipvalidator.cpp \
    clockform.cpp \
    upgradeform.cpp

HEADERS  += mainwindow.h \
    disksform.h \
    licenseform.h \
    networkform.h \
    progressform.h \
    diskinfo.h \
    applogic.h \
    appdata.h \
    netsettings.h \
    ifinfo.h \
    confirmform.h \
    messagebox.h \
    ipvalidator.h \
    clockform.h \
    zoneinfo.h \
    upgradeform.h

FORMS    += mainwindow.ui \
    disksform.ui \
    licenseform.ui \
    networkform.ui \
    progressform.ui \
    templateform.ui \
    confirmform.ui \
    clockform.ui \
    upgradeform.ui

RESOURCES += \
    resources.qrc

OTHER_FILES += \
    scripts/detect-disks.sh \
    scripts/install.sh \
    scripts/s1-format-disk.sh \
    scripts/s3-install-rootfs.sh \
    scripts/s2-install-kernel.sh \
    scripts/s4-install-packages.sh \
    scripts/s5-set-password.sh \
    scripts/s6-configure-network.sh \
    scripts/s7-configure-ssh.sh \
    scripts/get-net-settings.sh \
    scripts/s8-configure-repos.sh \
    scripts/s9-create-initrd.sh \
    scripts/s10-install-bootloader.sh \
    scripts/detect-interfaces.sh \
    scripts/s11-post-install.sh \
    scripts/detect-install-device.sh \
    scripts/eject-device.sh

DISTFILES += \
    scripts/s5-set-time.sh \
    scripts/upgrade/get_ps_disk.sh \
    scripts/upgrade/get_ps_version.sh \
    scripts/upgrade/1.2.0/u1-pre-install.sh \
    scripts/upgrade/1.2.0/u2-format-disk.sh \
    scripts/upgrade/1.2.0/u3-install-kernel.sh \
    scripts/upgrade/1.2.0/u4-install-rootfs.sh \
    scripts/upgrade/1.2.0/u5-install-packages.sh \
    scripts/upgrade/1.2.0/u6-configure-ssh.sh \
    scripts/upgrade/1.2.0/u7-configure-repos.sh \
    scripts/upgrade/1.2.0/u8-create-initrd.sh \
    scripts/upgrade/1.2.0/u9-install-bootloader.sh \
    scripts/upgrade/1.2.0/u10-post-install.sh \
    scripts/upgrade/1.2.1/u1-pre-install.sh \
    scripts/upgrade/1.2.1/u2-format-disk.sh \
    scripts/upgrade/1.2.1/u3-install-kernel.sh \
    scripts/upgrade/1.2.1/u4-install-rootfs.sh \
    scripts/upgrade/1.2.1/u5-install-packages.sh \
    scripts/upgrade/1.2.1/u6-configure-ssh.sh \
    scripts/upgrade/1.2.1/u7-configure-repos.sh \
    scripts/upgrade/1.2.1/u8-create-initrd.sh \
    scripts/upgrade/1.2.1/u9-install-bootloader.sh \
    scripts/upgrade/1.2.1/u10-post-install.sh \
    scripts/upgrade/1.2.2/u1-pre-install.sh \
    scripts/upgrade/1.2.2/u2-format-disk.sh \
    scripts/upgrade/1.2.2/u3-install-kernel.sh \
    scripts/upgrade/1.2.2/u4-install-rootfs.sh \
    scripts/upgrade/1.2.2/u5-install-packages.sh \
    scripts/upgrade/1.2.2/u6-configure-ssh.sh \
    scripts/upgrade/1.2.2/u7-configure-repos.sh \
    scripts/upgrade/1.2.2/u8-create-initrd.sh \
    scripts/upgrade/1.2.2/u9-install-bootloader.sh \
    scripts/upgrade/1.2.2/u10-post-install.sh \
    scripts/upgrade/1.3.0/u1-pre-install.sh \
    scripts/upgrade/1.3.0/u10-post-install.sh \
    scripts/upgrade/1.3.0/u2-format-disk.sh \
    scripts/upgrade/1.3.0/u3-install-kernel.sh \
    scripts/upgrade/1.3.0/u4-install-rootfs.sh \
    scripts/upgrade/1.3.0/u5-install-packages.sh \
    scripts/upgrade/1.3.0/u6-configure-ssh.sh \
    scripts/upgrade/1.3.0/u7-configure-repos.sh \
    scripts/upgrade/1.3.0/u8-create-initrd.sh \
    scripts/upgrade/1.3.0/u9-install-bootloader.sh \
    scripts/upgrade/1.3.1/u1-pre-install.sh \
    scripts/upgrade/1.3.1/u10-post-install.sh \
    scripts/upgrade/1.3.1/u2-format-disk.sh \
    scripts/upgrade/1.3.1/u3-install-kernel.sh \
    scripts/upgrade/1.3.1/u4-install-rootfs.sh \
    scripts/upgrade/1.3.1/u5-install-packages.sh \
    scripts/upgrade/1.3.1/u6-configure-ssh.sh \
    scripts/upgrade/1.3.1/u7-configure-repos.sh \
    scripts/upgrade/1.3.1/u8-create-initrd.sh \
    scripts/upgrade/1.3.1/u9-install-bootloader.sh \
    scripts/upgrade/1.4.0/u1-pre-install.sh \
    scripts/upgrade/1.4.0/u10-post-install.sh \
    scripts/upgrade/1.4.0/u2-format-disk.sh \
    scripts/upgrade/1.4.0/u3-install-kernel.sh \
    scripts/upgrade/1.4.0/u4-install-rootfs.sh \
    scripts/upgrade/1.4.0/u5-install-packages.sh \
    scripts/upgrade/1.4.0/u6-configure-ssh.sh \
    scripts/upgrade/1.4.0/u7-configure-repos.sh \
    scripts/upgrade/1.4.0/u8-create-initrd.sh \
    scripts/upgrade/1.4.0/u9-install-bootloader.sh \
    scripts/upgrade/1.5.0/u1-pre-install.sh \
    scripts/upgrade/1.5.0/u10-post-install.sh \
    scripts/upgrade/1.5.0/u2-format-disk.sh \
    scripts/upgrade/1.5.0/u3-install-kernel.sh \
    scripts/upgrade/1.5.0/u4-install-rootfs.sh \
    scripts/upgrade/1.5.0/u5-install-packages.sh \
    scripts/upgrade/1.5.0/u6-configure-ssh.sh \
    scripts/upgrade/1.5.0/u7-configure-repos.sh \
    scripts/upgrade/1.5.0/u8-create-initrd.sh \
    scripts/upgrade/1.5.0/u9-install-bootloader.sh \
    scripts/upgrade/2.0.0/u1-pre-install.sh \
    scripts/upgrade/2.0.0/u2-format-disk.sh \
    scripts/upgrade/2.0.0/u3-install-kernel.sh \
    scripts/upgrade/2.0.0/u4-install-rootfs.sh \
    scripts/upgrade/2.0.0/u5-install-packages.sh \
    scripts/upgrade/2.0.0/u6-configure-ssh.sh \
    scripts/upgrade/2.0.0/u7-configure-repos.sh \
    scripts/upgrade/2.0.0/u8-create-initrd.sh \
    scripts/upgrade/2.0.0/u9-install-bootloader.sh \
    scripts/upgrade/2.0.0/u10-post-install.sh \
    scripts/s2-install-rootfs.sh \
    scripts/s3-set-time.sh \
    scripts/s4-configure-network.sh \
    scripts/s5-create-initrd.sh \
    scripts/s6-install-bootloader.sh \
    scripts/s7-post-install.sh \
    scripts/sX-set-password.sh \
    scripts/upgrade/2.1.0/u1-pre-install.sh \
    scripts/upgrade/2.1.0/u2-format-disk.sh \
    scripts/upgrade/2.1.0/u3-install-rootfs.sh \
    scripts/upgrade/2.1.0/u4-create-initrd.sh \
    scripts/upgrade/2.1.0/u5-install-bootloader.sh \
    scripts/upgrade/2.1.0/u6-post-install.sh \
    scripts/upgrade/2.0.0/u1-pre-install.sh \
    scripts/upgrade/2.0.0/u1-pre-install.sh \
    scripts/upgrade/2.0.0/u2-format-disk.sh \
    scripts/upgrade/2.0.0/u3-install-rootfs.sh \
    scripts/upgrade/2.0.0/u4-create-initrd.sh \
    scripts/upgrade/2.0.0/u5-install-bootloader.sh \
    scripts/upgrade/2.0.0/u6-post-install.sh \
    scripts/upgrade/2.3.0/u1-pre-install.sh \
    scripts/upgrade/2.3.0/u2-format-disk.sh \
    scripts/upgrade/2.3.0/u3-install-rootfs.sh \
    scripts/upgrade/2.3.0/u4-create-initrd.sh \
    scripts/upgrade/2.3.0/u5-install-bootloader.sh \
    scripts/upgrade/2.3.0/u6-post-install.sh \
    scripts/upgrade/2.3.1/u1-pre-install.sh \
    scripts/upgrade/2.3.1/u2-format-disk.sh \
    scripts/upgrade/2.3.1/u3-install-rootfs.sh \
    scripts/upgrade/2.3.1/u4-create-initrd.sh \
    scripts/upgrade/2.3.1/u5-install-bootloader.sh \
    scripts/upgrade/2.3.1/u6-post-install.sh

