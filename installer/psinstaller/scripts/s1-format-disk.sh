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


dd if=/dev/zero of=$DEVICE  bs=1k count=1
sync
sleep $SLEEP_SEC

sgdisk --clear $DEVICE

sgdisk --new 1::+1M   --typecode=1:ef02 --change-name=1:'BIOS boot partition' $DEVICE
sgdisk --new 2::+128M --typecode=2:ef00 --change-name=2:'EFI System' $DEVICE
sgdisk --new 3::+15G  --typecode=3:8300 --change-name=3:'PetaSAN root filesystem' $DEVICE
sgdisk --new 4::+30G  --typecode=4:8300 --change-name=4:'Ceph data' $DEVICE
sgdisk --new 5::-0    --typecode=4:8300 --change-name=5:'PetaSAN data' $DEVICE


sleep $SLEEP_SEC
partprobe $DEVICE
sync
sleep $SLEEP_SEC
udevadm trigger --subsystem-match block
udevadm settle --timeout 10

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

mkdir -p /mnt/ceph_data
mkfs.ext4 -F -m 0 $(partition_name $DEVICE 4)
sync
sleep $SLEEP_SEC
mount $(partition_name $DEVICE 4) /mnt/ceph_data


mkdir -p /mnt/petasan_data
mkfs.ext4 -F -m 0 $(partition_name $DEVICE 5)
sync
sleep $SLEEP_SEC
mount $(partition_name $DEVICE 5) /mnt/petasan_data


sync
sleep $SLEEP_SEC

# populate /dev/disk/by-uuid for grub-update
ROOT_PART=$(partition_name $DEVICE 3)
udevadm trigger --action=add --sysname-match $(basename $ROOT_PART)
udevadm settle --timeout 10




