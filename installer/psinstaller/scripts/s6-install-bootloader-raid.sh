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

KERNEL=$(uname -r)
ROOTFS_LABEL="PetaSANSystem"

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



EFI_UUID=$(blkid -s UUID -o value $(partition_name $DEVICE_A 2) )
ROOTFS_UUID=$(blkid -s UUID -o value /dev/md/PETASAN_OS )

e2label /dev/md/PETASAN_OS $ROOTFS_LABEL

chroot /mnt/rootfs/ grub-install --target=i386-pc --modules="ext2 part_gpt mdraid1x" $DEVICE_A
chroot /mnt/rootfs/ grub-install --target=i386-pc --modules="ext2 part_gpt mdraid1x" $DEVICE_B


mkdir -p /mnt/efi/EFI/BOOT
grub-mkimage -d /usr/lib/grub/x86_64-efi -o /mnt/efi/EFI/BOOT/bootx64.efi -p /EFI/BOOT -O x86_64-efi \
fat iso9660 part_gpt part_msdos normal boot linux configfile loopback chain efifwsetup efi_gop  efi_uga \
ls search search_label search_fs_uuid search_fs_file gfxterm gfxterm_background gfxterm_menu test \
all_video loadenv exfat ext2 ntfs btrfs hfsplus udf mdraid1x



# config file for bios
cat << EOF    >  /mnt/rootfs/boot/grub/grub.cfg
set timeout=0
set default=0

menuentry 'PetaSAN' {
	insmod gzio
	insmod part_gpt
	insmod ext2
	insmod mdraid1x
	#set root='mduuid/837a70dcc9aa7ae244dd30ac27029d9e'
	set root='md/PETASAN_OS'

	search --no-floppy --fs-uuid --set=root $ROOTFS_UUID
        linux  /boot/vmlinuz-$KERNEL root=UUID=$ROOTFS_UUID quiet net.ifnames=0 intel_idle.max_cstate=1 processor.max_cstate=1
	initrd /boot/initrd.img-$KERNEL 
}
EOF


# config file for efi: make a copy
cp /mnt/rootfs/boot/grub/grub.cfg /mnt/efi/EFI/BOOT

# clone efi partition, the same UUID will be on both partitions
dd if=$(partition_name $DEVICE_A 2) of=$(partition_name $DEVICE_B 2)


cat << EOF    >  /mnt/rootfs/etc/fstab
/dev/md/PETASAN_OS / ext4 defaults 0 0
/dev/md/PETASAN_CEPH /var/lib/ceph ext4 defaults 0 0
/dev/md/PETASAN_DATA /opt/petasan/config ext4 defaults 0 0

UUID=$EFI_UUID /opt/petasan/config ext4 defaults 0 0
EOF

sync

