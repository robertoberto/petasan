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


PS_DEVICE=$(blkid -lt LABEL=$PS_ROOTFS_LABEL -o device)
if [ -z "$PS_DEVICE" ];
  then
    exit 1
  fi

PS_DEVICE=${PS_DEVICE#/dev/}
PS_DISK=$(readlink /sys/class/block/$PS_DEVICE)
PS_DISK=${PS_DISK%/*}
PS_DISK=/dev/${PS_DISK##*/}
echo $PS_DISK


