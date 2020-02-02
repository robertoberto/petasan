#!/bin/sh
# Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
# Copyright (C) 2019 PetaSAN www.petasan.org


# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.



PS_ROOTFS_LABEL=PetaSANSystem
SLEEP_SEC=3

PS_DEVICE=$(blkid -lt LABEL=$PS_ROOTFS_LABEL -o device)
if [ -z "$PS_DEVICE" ];
  then
    exit 1
  fi

mkdir -p /mnt/rootfs
mount $PS_DEVICE /mnt/rootfs

chroot /mnt/rootfs /bin/sh  << EOF
 #dpkg -l petasan | grep ii | tr -s ' '   | cut -d ' ' -f3
 dpkg -s petasan | grep -i Version | tr -s ' ' | cut -d ' ' -f2
EOF


while mount | grep /mnt/rootfs ;  do
umount /mnt/rootfs
sync
sleep $SLEEP_SEC
done
sync
sleep $SLEEP_SEC









