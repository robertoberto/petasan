#!/bin/sh -e
# Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
# Copyright (C) 2019 PetaSAN www.petasan.org


# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.


if [ -f  /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
  sleep 50
  echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
fi
if [ -f  /sys/devices/system/cpu/intel_pstate/min_perf_pct ]; then
  sleep 50
  echo 100 > /sys/devices/system/cpu/intel_pstate/min_perf_pct
fi
exit 0
