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



DEVICE=$1
SLEEP_SEC=3

partition_name() {
DEV=$1
PART_NUM=$2

#if [[ "$DEV" =~ ^/dev/nvme[0-9]{1,2}n ]]
if [[ "$DEV" =~ ^/dev/nvme ]]
then
  echo ${DEV}p$PART_NUM
else
  echo $DEV$PART_NUM
fi
}

mkdir -p /mnt/rootfs
mkdir -p /mnt/petasan_data

partition_type() {
# fdisk -l $1 | grep "Disklabel type:" |awk '{ print $3 }'
parted $1 print  | grep "Partition Table:" |awk '{ print $3 }'
}

if [ $(partition_type $DEVICE) = "gpt" ]
then
  mount $(partition_name $DEVICE 3) /mnt/rootfs
  mount $(partition_name $DEVICE 5) /mnt/petasan_data
else
  mount $(partition_name $DEVICE 2) /mnt/rootfs
  mount $(partition_name $DEVICE 4) /mnt/petasan_data
fi


cp /mnt/rootfs/etc/passwd /mnt/petasan_data/etc
cp /mnt/rootfs/etc/shadow /mnt/petasan_data/etc
cp /mnt/rootfs/etc/hostname /mnt/petasan_data/etc


if [ -f /mnt/rootfs/etc/udev/rules.d/70-persistent-net.rules ];
then
  mkdir -p /mnt/petasan_data/etc/udev/rules.d
  cp /mnt/rootfs/etc/udev/rules.d/70-persistent-net.rules /mnt/petasan_data/etc/udev/rules.d
fi

if [ -f /mnt/rootfs/etc/udev/rules.d/90-petasan-disk.rules ];
then
  mkdir -p /mnt/petasan_data/etc/udev/rules.d
  cp /mnt/rootfs/etc/udev/rules.d/90-petasan-disk.rules /mnt/petasan_data/etc/udev/rules.d
fi

if [ -f /mnt/rootfs/etc/sysctl.conf ];
then
  mkdir -p /mnt/petasan_data/etc
  cp /mnt/rootfs/etc/sysctl.conf /mnt/petasan_data/etc
fi


while mount | grep /mnt/rootfs ;  do
umount /mnt/rootfs
sync
sleep $SLEEP_SEC
done
sync
sleep $SLEEP_SEC


echo "Pre-install complete."






