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

mkdir -p /mnt/rootfs/var/lib/ceph
mount -o bind /mnt/ceph_data /mnt/rootfs/var/lib/ceph

mkdir -p /mnt/rootfs/opt/petasan/config
mount -o bind /mnt/petasan_data /mnt/rootfs/opt/petasan/config

mkdir -p /mnt/rootfs/debs
mount -o bind /mnt/cdrom/debs /mnt/rootfs/debs

sync
sleep $SLEEP_SEC

unsquashfs -f -i -d /mnt/rootfs /mnt/cdrom/petasan.squashfs

sync
sleep $SLEEP_SEC


chroot /mnt/rootfs /bin/bash  << EOF
 export DEBIAN_FRONTEND=noninteractive
 export DEBIAN_PRIORITY=critical
 dpkg -i /debs/*.deb
EOF

mdadm --examine --scan > /mnt/rootfs/etc/mdadm/mdadm.conf

mount --bind /sys  /mnt/rootfs/sys
mount --bind /proc /mnt/rootfs/proc
mount --bind /dev  /mnt/rootfs/dev

sync
sleep $SLEEP_SEC





