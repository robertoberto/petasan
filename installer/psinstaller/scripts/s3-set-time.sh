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




#DATE=$(date "+%Y-%m-%d %H:%M:%S" )

DATE=$1
ZONE=$2

chroot /mnt/rootfs /bin/bash  << EOF
rm /etc/localtime
ln -s  /usr/share/zoneinfo/$ZONE  /etc/localtime
date "-s $DATE"
hwclock --systohc --utc
EOF








