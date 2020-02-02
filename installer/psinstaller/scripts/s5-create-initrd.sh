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



echo -e "# SUSE-unsupported feature METADATA_CSUM\noptions ext4 allow_unsupported=1" \
> /mnt/rootfs/etc/modprobe.d/20-ext4.conf

KERNEL=$(uname -r)
chroot /mnt/rootfs/ update-initramfs -c -v -k  $KERNEL


