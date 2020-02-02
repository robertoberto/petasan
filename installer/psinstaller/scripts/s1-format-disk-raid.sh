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




DEVICE_A=$1
DEVICE_B=$2

#DEVICE_A="/dev/sda"
#DEVICE_B="/dev/sdb"

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


wipefs --all --force $DEVICE_A
wipefs --all --force $DEVICE_B
dd if=/dev/zero of=$DEVICE_A  bs=1k count=1
dd if=/dev/zero of=$DEVICE_B  bs=1k count=1
sync
sleep $SLEEP_SEC

sgdisk --new 1::+1M   --typecode=1:ef02 --change-name=1:'BIOS boot partition' $DEVICE_A
sgdisk --new 2::+128M --typecode=2:ef00 --change-name=2:'EFI System' $DEVICE_A
sgdisk --new 3::+15G  --typecode=3:fd00 --change-name=3:'PetaSAN root filesystem' $DEVICE_A
sgdisk --new 4::+30G  --typecode=4:fd00 --change-name=4:'Ceph data' $DEVICE_A
sgdisk --new 5::-0    --typecode=5:fd00 --change-name=5:'PetaSAN data' $DEVICE_A


udevadm trigger --subsystem-match block
udevadm settle --timeout 10

partprobe $DEVICE_A
sync
sleep $SLEEP_SEC

sfdisk -d $DEVICE_A | sfdisk --force $DEVICE_B

udevadm trigger --subsystem-match block
udevadm settle --timeout 10

partprobe $DEVICE_B
sync
sleep $SLEEP_SEC


mdadm --zero-superblock $(partition_name $DEVICE_A 3)
mdadm --zero-superblock $(partition_name $DEVICE_A 4)
mdadm --zero-superblock $(partition_name $DEVICE_A 5)

mdadm --zero-superblock $(partition_name $DEVICE_B 3)
mdadm --zero-superblock $(partition_name $DEVICE_B 4)
mdadm --zero-superblock $(partition_name $DEVICE_B 5)


yes | mdadm --create /dev/md/PETASAN_OS --level=1 --raid-disks=2 --name=PETASAN_OS \ 
$(partition_name $DEVICE_A 3) $(partition_name $DEVICE_B 3)
  
yes | mdadm --create /dev/md/PETASAN_CEPH --level=1 --raid-disks=2 --name=PETASAN_CEPH \ 
$(partition_name $DEVICE_A 4) $(partition_name $DEVICE_B 4)
  
yes | mdadm --create /dev/md/PETASAN_DATA --level=1 --raid-disks=2 --name=PETASAN_DATA \ 
$(partition_name $DEVICE_A 5) $(partition_name $DEVICE_B 5)
  
  
# cannot raid efi, will clone it at end 
mkdir -p /mnt/efi
mkfs.fat -F32 $(partition_name $DEVICE_A 2)
sync
sleep $SLEEP_SEC
mount $(partition_name $DEVICE_A 2) /mnt/efi


mkdir -p /mnt/rootfs
mkfs.ext4 -F -m 0 -L $ROOTFS_LABEL /dev/md/PETASAN_OS
sync
sleep $SLEEP_SEC
mount /dev/md/PETASAN_OS /mnt/rootfs

mkdir -p /mnt/ceph_data
mkfs.ext4 -F -m 0 $(partition_name /dev/md/PETASAN_CEPH
sync
sleep $SLEEP_SEC
mount /dev/md/PETASAN_CEPH /mnt/ceph_data


mkdir -p /mnt/petasan_data
mkfs.ext4 -F -m 0 /dev/md/PETASAN_DATA
sync
sleep $SLEEP_SEC
mount /dev/md/PETASAN_DATA /mnt/petasan_data


sync
sleep $SLEEP_SEC




