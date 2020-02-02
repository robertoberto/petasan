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
ROOTFS_LABEL="PetaSANSystem"
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

while mount | grep /mnt/rootfs ;  do
umount /mnt/rootfs
sync
sleep $SLEEP_SEC
done
umount -f /mnt/rootfs
sync
sleep $SLEEP_SEC


partition_type() {
# fdisk -l $1 | grep "Disklabel type:" |awk '{ print $3 }'
parted $1 print  | grep "Partition Table:" |awk '{ print $3 }'
}

if [ $(partition_type $DEVICE) = "gpt" ]
then

  mkdir -p /mnt/efi
  mkfs.fat -F32 $(partition_name $DEVICE 2)
  sync
  sleep $SLEEP_SEC
  mount $(partition_name $DEVICE 2) /mnt/efi

  mkdir -p /mnt/rootfs
  mkfs.ext4 -F -m 0 -L $ROOTFS_LABEL $(partition_name $DEVICE 3)
  sync
  sleep $SLEEP_SEC
  mount $(partition_name $DEVICE 3) /mnt/rootfs

  mkdir -p /mnt/ceph_varlib
  mount $(partition_name $DEVICE 4) /mnt/ceph_varlib

  mkdir -p /mnt/petasan_data
  mount $(partition_name $DEVICE 5) /mnt/petasan_data

  sync
  sleep $SLEEP_SEC

  # populate /dev/disk/by-uuid for grub-update
  ROOT_PART=$(partition_name $DEVICE 3)
  udevadm trigger --action=add --sysname-match $(basename $ROOT_PART)
  udevadm settle --timeout 10

else

  mkdir -p /mnt/rootfs
  mkfs.ext4 -F -m 0 $(partition_name $DEVICE 2)
  sync
  sleep $SLEEP_SEC
  mount $(partition_name $DEVICE 2) /mnt/rootfs

  mkfs.ext4 -F -m 0 $(partition_name $DEVICE 1)
  sync 
  sleep $SLEEP_SEC
  #mkdir -p /mnt/rootfs/boot
  #mount ${DEVICE}1 /mnt/rootfs/boot

  mkdir -p /mnt/ceph_varlib
  mount $(partition_name $DEVICE 3) /mnt/ceph_varlib

  mkdir -p /mnt/petasan_data
  mount $(partition_name $DEVICE 4) /mnt/petasan_data

  sync
  sleep $SLEEP_SEC

  # populate /dev/disk/by-uuid for grub-update
  ROOT_PART=$(partition_name $DEVICE 2)
  udevadm trigger --action=add --sysname-match $(basename $ROOT_PART)
  udevadm settle --timeout 10

fi

sync
sleep $SLEEP_SEC

echo Formatting complete





