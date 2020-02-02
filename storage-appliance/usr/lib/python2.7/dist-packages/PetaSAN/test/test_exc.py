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

import subprocess
import os
import sys
import threading


# subprocess.Popen('consul agent -config-dir /etc/consul.d/server -bind 192.168.17.12  -retry-join 192.168.17.11 -retry-join 192.168.17.10 # &',stdout=subprocess.PIPE)

'''def task():

	subprocess.Popen('consul agent -config-dir /etc/consul.d/server -bind 192.168.17.12  -retry-join 192.168.17.11 -retry-join 192.168.17.10 ', shell=True)
t = threading.Thread(name='my_service', target=task)
t.start()
print "test >>>>>>>> >>>>>>>>>>>"
#close_fds=True
'''

os.system('consul agent -config-dir /etc/consul.d/server -bind 192.168.17.12  -retry-join 192.168.17.11 -retry-join 192.168.17.10 ')