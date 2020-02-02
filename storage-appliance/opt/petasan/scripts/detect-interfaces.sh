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



for DEVICE_PATH in $(find /sys/class/net/* | grep -E '\/(eth)' | grep -v '\.')
 do
  DEVICE=${DEVICE_PATH##*/}
  PCI=$(udevadm info -a -p /sys/class/net/$DEVICE | awk -F/ '/device.*eth/ {print $5}' | cut -c6- )
  MODEL=$(lspci | grep $PCI  | cut -d ':' -f3 | tr , ' ' | awk '{$1=$1};1')
  MAC=$(ethtool -P $DEVICE | cut -d ' ' -f3)
  echo  device=$DEVICE,mac=$MAC,pci=$PCI,model=$MODEL
done


