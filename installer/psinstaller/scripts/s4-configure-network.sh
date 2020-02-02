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




HOSTNAME=$1
IFACE=$2
IP=$3
MASK=$4
GATEWAY=$5
DNS=$6
VLAN=$7

if [ ! -d  "/mnt/rootfs/etc/network" ]
then
  mkdir -p /mnt/rootfs/etc/network
fi

#echo "auto eth0" >> /mnt/rootfs/etc/network/interfaces
#echo "iface eth0 inet dhcp" >> /mnt/rootfs/etc/network/interfaces

echo  $HOSTNAME > /mnt/rootfs/etc/hostname

echo "127.0.0.1   localhost" > /mnt/rootfs/etc/hosts
echo "$IP   $HOSTNAME" >> /mnt/rootfs/etc/hosts

rm -f /mnt/rootfs/etc/resolv.conf
echo "nameserver   $DNS" > /mnt/rootfs/etc/resolv.conf


if [ -n "$VLAN" ]
then
  IFACE="$IFACE.$VLAN"
fi
cat << EOF    >  /mnt/rootfs/etc/network/interfaces
auto $IFACE
iface $IFACE inet static
        address $IP
        netmask $MASK
        gateway $GATEWAY
        dns-nameservers $DNS
EOF

echo network configuration complete.

