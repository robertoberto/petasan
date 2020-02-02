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

chroot /mnt/rootfs /bin/bash  << EOF

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

# ----- New Installation  ----------

# /persistent_net_rules
/opt/petasan/scripts/installer/persistent_net_rules.py

useradd -d /home/ceph -m ceph

mkdir -p /opt/petasan/config/shared
mkdir -p /opt/petasan/config/gfs-brick

# create sym links

mkdir -p /opt/petasan/config/etc/ceph
rm -rf /etc/ceph
ln -s /opt/petasan/config/etc/ceph /etc/ceph

mkdir -p /opt/petasan/config/etc
cp /etc/hosts /opt/petasan/config/etc
rm -f /etc/hosts
ln -s /opt/petasan/config/etc/hosts /etc/hosts

cp -r /etc/ssh /opt/petasan/config/etc
rm -rf /etc/ssh
ln -s /opt/petasan/config/etc/ssh /etc/ssh

if [ -d /root/.ssh  ]; then
  mkdir -p /opt/petasan/config/root
  cp -r  /root/.ssh /opt/petasan/config/root
  rm -rf /root/.ssh
else
  mkdir -p /opt/petasan/config/root/.ssh
fi
ln -s /opt/petasan/config/root/.ssh /root/.ssh

mkdir -p /opt/petasan/config/etc/network
cp -f /etc/network/interfaces /opt/petasan/config/etc/network
rm -f /etc/network/interfaces
ln -s /opt/petasan/config/etc/network/interfaces  /etc/network/interfaces

cp /etc/resolv.conf /opt/petasan/config/etc
rm -f /etc/resolv.conf
ln -s /opt/petasan/config/etc/resolv.conf /etc/resolv.conf

cp /etc/ntp.conf /opt/petasan/config/etc
rm -f /etc/ntp.conf
ln -s /opt/petasan/config/etc/ntp.conf /etc/ntp.conf

readlink /etc/localtime  > /opt/petasan/config/etc/tz

mkdir -p /opt/petasan/config/var/lib
cp -rf /var/lib/glusterd  /opt/petasan/config/var/lib
rm -rf /var/lib/glusterd
ln -s /opt/petasan/config/var/lib/glusterd /var/lib/glusterd


# sym links do not work for these, just keep a copy in config
cp  /etc/hostname /opt/petasan/config/etc/hostname
cp /etc/passwd /opt/petasan/config/etc
cp /etc/shadow /opt/petasan/config/etc

EOF

sync
sleep $SLEEP_SEC




