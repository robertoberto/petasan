#!/bin/bash
# Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
# Copyright (C) 2019 PetaSAN www.petasan.org


# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.



SLEEP_SEC=3

# clean newly installed /var/lib/ceph
rm -rf   /mnt/rootfs/var/lib/ceph
mkdir -p /mnt/rootfs/var/lib/ceph
# mount existing /var/lib/ceph for upgrade cluster name
mount -o bind /mnt/ceph_varlib /mnt/rootfs/var/lib/ceph

# Step1: Before bind mounting existing config partition :
# delete newly installed /opt/petasan/config, but first copy any newly added files to existing config

# copy new stat files
#cp /mnt/rootfs/opt/petasan/config/stats/grafana/grafana.db /mnt/petasan_data/stats/grafana
cp -rf /mnt/rootfs/opt/petasan/config/stats /mnt/petasan_data

# copy new json config files
cp /mnt/rootfs/opt/petasan/config/pages.json /mnt/petasan_data
cp /mnt/rootfs/opt/petasan/config/rolepages.json /mnt/petasan_data
cp /mnt/rootfs/opt/petasan/config/roles.json /mnt/petasan_data

# copy new templates
mkdir -p /mnt/petasan_data/crush
cp -rf /mnt/rootfs/opt/petasan/config/crush/rule_templates /mnt/petasan_data/crush

# now delete and mount existing config
rm -rf   /mnt/rootfs/opt/petasan/config
mkdir -p /mnt/rootfs/opt/petasan/config
mount -o bind /mnt/petasan_data /mnt/rootfs/opt/petasan/config


HOST_NAME=$(cat /mnt/rootfs/opt/petasan/config/etc/hostname)
TZ=$(cat /mnt/rootfs/opt/petasan/config/etc/tz)

# apply patches
patch -p1 --forward -d  /mnt/rootfs  <<'EOF'
--- a/usr/lib/python2.7/dist-packages/dialog.py
+++ b/usr/lib/python2.7/dist-packages/dialog.py
@@ -1221,10 +1221,7 @@ class Dialog(object):
         l = ['"']
 
         for c in argument:
-            if c in ('"', '\\'):
-                l.append("\\" + c)
-            else:
-                l.append(c)
+	    l.append(c)
 
         return ''.join(l + ['"'])
EOF

# Step2: chroot

chroot /mnt/rootfs /bin/bash  << EOF

HOST_NAME2=$(cat /opt/petasan/config/etc/hostname)
TZ2=$(cat /opt/petasan/config/etc/tz)

update-rc.d ntp disable
systemctl disable ntp
systemctl disable systemd-timesyncd
systemctl disable carbon-cache
systemctl disable apache2
systemctl disable collectd
systemctl disable grafana-server
systemctl disable glusterd
systemctl disable petasan-mount-sharedfs
systemctl disable petasan-cluster-leader
systemctl disable petasan-start-osds

systemctl disable smartd
systemctl disable smartmontools
systemctl disable sysstat

systemctl enable  petasan-deploy.service
systemctl enable  petasan-console.service
systemctl enable  petasan-start-services.service

# Bionic
systemctl disable  glustereventsd

# Nautilus
systemctl disable ceph-crash

# SSH configuration 
update-rc.d ssh defaults 
# server
mkdir -p /run/sshd
sed -i -- 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/g'  /etc/ssh/sshd_config
echo "UseDNS no" >>  /etc/ssh/sshd_config
echo "GSSAPIAuthentication no" >>  /etc/ssh/sshd_config
# client
sed -i -- 's/GSSAPIAuthentication yes/GSSAPIAuthentication no/g'  /etc/ssh/ssh_config
echo "ServerAliveInterval 5 " >>  /etc/ssh/ssh_config
echo "ServerAliveCountMax 2 " >>  /etc/ssh/ssh_config


cat << EOF2    >  /etc/apt/sources.list

# PetaSAN updates
deb http://archive.petasan.org/repo/  petasan-v2 updates

# main
deb http://archive.ubuntu.com/ubuntu/ bionic main 
deb http://archive.ubuntu.com/ubuntu/ bionic-updates main 
deb http://archive.ubuntu.com/ubuntu/ bionic-security main 

# universe
#deb http://archive.ubuntu.com/ubuntu/ bionic universe
#deb http://archive.ubuntu.com/ubuntu/ bionic-updates universe
#deb http://archive.ubuntu.com/ubuntu/ bionic-security universe

# multiverse universe
#deb http://archive.ubuntu.com/ubuntu/ bionic multiverse
#deb http://archive.ubuntu.com/ubuntu/ bionic-updates multiverse
#deb http://archive.ubuntu.com/ubuntu/ bionic-security multiverse

EOF2

# set priority
cat << EOF2  >  /etc/apt/preferences.d/90-petasan
Package: *
Pin: release o=PetaSAN
Pin-Priority: 700
EOF2


mkdir -p     /opt/petasan/log
touch        /opt/petasan/log/PetaSAN.log
chmod 777    /opt/petasan/log/PetaSAN.log
mkdir -p     /opt/petasan/jobs
chmod -R 777 /opt/petasan/jobs
mkdir -p     /opt/petasan/config/crush/backup
chmod -R 777 /opt/petasan/config/crush/backup
mkdir -p     /opt/petasan/config/replication
chmod -R 777 /opt/petasan/config/replication

# console fonts
sed -i -- 's/FONTFACE=\"VGA\"/FONTFACE=\"Fixed\"/g'  /etc/default/console-setup

ln -s /opt/petasan/scripts/cron-1h.py /etc/cron.hourly/cron-1h
ln -s /opt/petasan/scripts/cron-1d.py /etc/cron.daily/cron-1d

# logrotate
mv /etc/cron.daily/logrotate /etc/cron.hourly
sed -i '5 i maxsize 100M\nminsize 100M\n' /etc/logrotate.conf

# ----- Uprade Installation  ----------

systemctl enable ceph.target

if grep -q '"is_management": true,' /opt/petasan/config/node_info.json
   then
   systemctl enable ceph-mon.target
   systemctl enable ceph-mon@$HOST_NAME

   systemctl enable ceph-mgr.target
   systemctl enable ceph-mgr@$HOST_NAME
fi


rm -rf /etc/ceph
ln -s /opt/petasan/config/etc/ceph /etc/ceph

rm -f /etc/hosts
ln -s /opt/petasan/config/etc/hosts /etc/hosts

rm -rf /etc/ssh
ln -s /opt/petasan/config/etc/ssh /etc/ssh

rm -rf /root/.ssh
ln -s /opt/petasan/config/root/.ssh /root/.ssh

rm -f /etc/network/interfaces
ln -s /opt/petasan/config/etc/network/interfaces  /etc/network/interfaces

rm -f /etc/resolv.conf
ln -s /opt/petasan/config/etc/resolv.conf /etc/resolv.conf


rm -f /etc/ntp.conf
ln -s /opt/petasan/config/etc/ntp.conf /etc/ntp.conf

rm -f /etc/localtime
ln -s $TZ  /etc/localtime

rm -rf /var/lib/glusterd  
ln -s /opt/petasan/config/var/lib/glusterd /var/lib/glusterd


# sym links do not work for these, need a copy

rm -f /etc/hostname
cp /opt/petasan/config/etc/hostname   /etc/hostname

#rm -f /etc/passwd
#cp  /opt/petasan/config/etc/passwd /etc/passwd

rm -f /etc/shadow
cp /opt/petasan/config/etc/shadow  /etc/shadow


if [ -f /opt/petasan/config/etc/udev/rules.d/70-persistent-net.rules ];
then
  cp /opt/petasan/config/etc/udev/rules.d/70-persistent-net.rules /etc/udev/rules.d
fi

if [ -f /opt/petasan/config/etc/udev/rules.d/90-petasan-disk.rules ];
then
  cp /opt/petasan/config/etc/udev/rules.d/90-petasan-disk.rules /etc/udev/rules.d
fi

if [ -f /opt/petasan/config/etc/sysctl.conf ];
then
  cp /opt/petasan/config/etc/sysctl.conf /etc
fi


chown -R ceph:ceph /var/lib/ceph/mon

# run any python upgrade scripts
#/opt/petasan/scripts/installer/upgrade/2.3.1/upgrade.py


sync
sleep $SLEEP_SEC
umount /mnt/rootfs
sync
sleep $SLEEP_SEC
INSTALLER_DEVICE=$(blkid -lt LABEL=PETASAN -o device)
umount $INSTALLER_DEVICE
sync
sleep $SLEEP_SEC





