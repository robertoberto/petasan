#! /usr/bin/python3
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

import time
import sys
import threading
import os
import json


counter = 0
previous_transfer = 0
current_transfer = 0
finished = False

class PipeReaderThread(threading.Thread):
    file_path = ""

    def __init__(self, file_path):
        threading.Thread.__init__(self)

        self.file_path = file_path



    def run(self):

        if os.path.exists(self.file_path):
            # start read transferred bytes
            data = {}
            while True:
                interval_time = 5
                global previous_transfer
                global counter
                global current_transfer
                global finished

                transferred_rate_per_interval = round (( float(current_transfer) - float(previous_transfer) ) / 1048576 , 2)
                transfer_rate = round (float(transferred_rate_per_interval) / interval_time, 2)
                data['transferred_bytes'] = str(round(current_transfer / 1073741824, 2)) + " GB"
                data['transfer_rate'] = str(transfer_rate) + " MB/s"
                for i in range(5):
                    try:
                        with open(self.file_path, 'w+') as outfile:
                            json.dump(data, outfile)
                        break

                    except:
                        time.sleep(2)
                        continue

                    # break

                previous_transfer = current_transfer

                if finished:
                    break
                time.sleep(interval_time)
        return



def read_bytes():
    global finished
    global current_transfer
    while True:
        data_stream = sys.stdin.buffer.read(4194304)

        if len(data_stream) == 0:
            finished = True
            break
        current_transfer = int(current_transfer)
        current_transfer += len(data_stream)
        sys.stdout.buffer.write(data_stream)



if __name__ == '__main__':
    if len(sys.argv) == 2:
        file_path = sys.argv[1]
        thread = PipeReaderThread(file_path)
        thread.start()
        read_bytes()
    else:
        sys.exit("Usage: [pipe_reader.py] [file path]")
