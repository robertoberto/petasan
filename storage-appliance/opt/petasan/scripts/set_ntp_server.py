#! /usr/bin/python
'''
 Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
 Copyright (C) 2019 PetaSAN www.petasan.org


 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU Affero General Public License
 as published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU Affero General Public License for more details.
'''


import sys
from PetaSAN.core.cluster.ntp import NTPConf

if len(sys.argv) != 2 :
	print 'usage: set_ntp_server  server_name'
	sys.exit(1)


server = sys.argv[1]
ntp = NTPConf()
ntp.set_ntp_server_local(server)
sys.exit(0)


