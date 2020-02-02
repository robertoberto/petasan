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
KERNEL=$(uname -r)
ROOTFS_LABEL="PetaSANSystem"


partition_name() {
DEV=$1
PART_NUM=$2
if [[ "$DEV" =~ ^/dev/nvme ]]
then
  echo ${DEV}p$PART_NUM
else
  echo $DEV$PART_NUM
fi
}

partition_type() {
parted $1 print  | grep "Partition Table:" |awk '{ print $3 }'
}

# Modify grub defaults

CMDLINE="\"quiet net.ifnames=0 intel_idle.max_cstate=1 processor.max_cstate=1 \
pti=off spectre_v2=off l1tf=off nospec_store_bypass_disable no_stf_barrier\""

sed -i "s/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT=$CMDLINE/g" /mnt/rootfs/etc/default/grub

sed -i "s/^GRUB_TIMEOUT_STYLE=.*/GRUB_TIMEOUT_STYLE=menu/g" /mnt/rootfs/etc/default/grub
sed -i "s/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/g" /mnt/rootfs/etc/default/grub
sed -i "s/echo Debian/echo PetaSAN/g" /mnt/rootfs/etc/default/grub
sed -i "s/GNU\/Linux/ /g" /mnt/rootfs/etc/grub.d/10_linux


if [ $(partition_type $DEVICE) = "gpt" ]

then
# ============ GPT ===================

e2label $(partition_name $DEVICE 3) $ROOTFS_LABEL

# install grub
if [ -d /sys/firmware/efi ]
then
  # ----------- efi ----------------------
  mkdir -p /mnt/rootfs/boot/efi
  mount -o bind /mnt/efi /mnt/rootfs/boot/efi
  chroot /mnt/rootfs/ grub-install --target=x86_64-efi --efi-directory=/boot/efi --no-floppy --bootloader-id=petasan
  # some firmware require BOOTx64.EFI
  mkdir -p /mnt/rootfs/boot/efi/EFI/BOOT
  cp /mnt/rootfs/boot/efi/EFI/petasan/grubx64.efi /mnt/rootfs/boot/efi/EFI/BOOT/BOOTx64.EFI
           
else
  # ----------- bios ----------------------
  chroot /mnt/rootfs/ grub-install --target=i386-pc --no-floppy $DEVICE
fi

# generate grub.cfg
chroot /mnt/rootfs/ update-grub

# generate fstab
EFI_UUID=$(blkid -s UUID -o value $(partition_name $DEVICE 2) )
ROOTFS_UUID=$(blkid -s UUID -o value $(partition_name $DEVICE 3) )
CEPH_DATA_UUID=$(blkid -s UUID -o value $(partition_name $DEVICE 4) )
PETASAN_DATA_UUID=$(blkid -s UUID -o value $(partition_name $DEVICE 5) )

cat << EOF    >  /mnt/rootfs/etc/fstab
UUID=$EFI_UUID /boot/efi vfat defaults 0 0
UUID=$ROOTFS_UUID / ext4 defaults 0 0
UUID=$CEPH_DATA_UUID /var/lib/ceph ext4 defaults 0 0
UUID=$PETASAN_DATA_UUID /opt/petasan/config ext4 defaults 0 0
EOF


else
# ============ BIOS / MBR ===================

e2label $(partition_name $DEVICE 2) $ROOTFS_LABEL

# install grub
chroot /mnt/rootfs/ grub-install --target=i386-pc --no-floppy $DEVICE

# generate grub.cfg
chroot /mnt/rootfs/ update-grub

# generate fstab
ROOTFS_UUID=$(blkid -s UUID -o value $(partition_name $DEVICE 2) )
CEPH_DATA_UUID=$(blkid -s UUID -o value $(partition_name $DEVICE 3) )
PETASAN_DATA_UUID=$(blkid -s UUID -o value $(partition_name $DEVICE 4) )

cat << EOF    >  /mnt/rootfs/etc/fstab
UUID=$ROOTFS_UUID / ext4 defaults 0 0
UUID=$CEPH_DATA_UUID /var/lib/ceph ext4 defaults 0 0
UUID=$PETASAN_DATA_UUID /opt/petasan/config ext4 defaults 0 0
EOF

fi

sync

