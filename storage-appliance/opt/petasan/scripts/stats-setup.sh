#! /bin/bash
# Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
# Copyright (C) 2019 PetaSAN www.petasan.org


# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.




SRC=/opt/petasan/config/stats

systemctl disable carbon-cache  >/dev/null 2>&1
systemctl disable apache2 >/dev/null 2>&1
systemctl disable collectd  >/dev/null 2>&1
systemctl disable grafana-server >/dev/null 2>&1

systemctl stop carbon-cache
systemctl stop apache2
systemctl stop collectd
systemctl stop grafana-server


# ----------   Carbon ---------------------
cp $SRC/carbon/*  /etc/carbon
chown -R _graphite /etc/carbon

if [ ! -d  /opt/petasan/config/shared/graphite ]; then
  mkdir -p /opt/petasan/config/shared/graphite
fi
chown -R _graphite /opt/petasan/config/shared/graphite

OLD_CLUSTER_STATS_PATH="/opt/petasan/config/shared/graphite/whisper/PetaSAN/storage-node"
NEW_CLUSTER_STATS_PATH="/opt/petasan/config/shared/graphite/whisper/PetaSAN/ClusterStats"
if [ -d "$OLD_CLUSTER_STATS_PATH" ] && [ ! -d "$NEW_CLUSTER_STATS_PATH" ] ; then
  mv $OLD_CLUSTER_STATS_PATH $NEW_CLUSTER_STATS_PATH
fi

# rename cluster name to ceph
if [ ! -d "/opt/petasan/config/shared/graphite/whisper/PetaSAN/ClusterStats/ceph-ceph" ] ; then
  /opt/petasan/scripts/installer/upgrade/2.3.0/cluster_name_stats.py

  mv /opt/petasan/config/shared/graphite/whisper/PetaSAN/ClusterStats/ceph-ceph/cluster\
     /opt/petasan/config/shared/graphite/whisper/PetaSAN/ClusterStats/ceph-ceph/pool-all

fi


# ----------   Graphite ---------------------

cp $SRC/graphite/local_settings.py /etc/graphite
cp $SRC/graphite/graphite.db /var/lib/graphite
chmod 666 /var/lib/graphite/graphite.db

#cp /usr/share/graphite-web/apache2-graphite.conf /etc/apache2/sites-available
cp $SRC/graphite/apache2-graphite.conf /etc/apache2/sites-available
cp $SRC/graphite/ports.conf /etc/apache2

a2dissite 000-default >/dev/null 2>&1
a2ensite apache2-graphite >/dev/null 2>&1

# ----------   Collectd ---------------------

CLUSTER_NAME="ceph"
#for file in "/etc/ceph/*.conf"; do
#  CLUSTER_NAME=$(basename -s .conf $file )
#  break
#done

cp $SRC/collectd/collectd.conf /etc/collectd
cp -rf $SRC/collectd/plugins /usr/lib/collectd
sed -i -- "s/CLUSTER_NAME/$CLUSTER_NAME/g"  /etc/collectd/collectd.conf

# ----------   Grafana ---------------------
cp $SRC/grafana/grafana.ini /etc/grafana
cp $SRC/grafana/grafana.db /var/lib/grafana
chown -R grafana /var/lib/grafana




