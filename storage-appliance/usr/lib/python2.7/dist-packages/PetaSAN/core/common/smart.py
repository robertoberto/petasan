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

import re
from PetaSAN.core.common.cmd import call_cmd, exec_command, exec_command_ex


class Smart(object):
    def __init__(self):
        pass

    # -------------------------------------------  "get_disk_list" Function  -------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def get_disk_list(self):
        """
        DOCSTRING : this function is to get a list of all disks located in a node
        Args : ---
        Returns : list of all disks located in a node
        """

        output, err = exec_command("smartctl --scan")
        disk_names = []

        for line in output.splitlines():
            disk_name = line[line.find('/dev/') + len('/dev/'):line.rfind(' -d')]
            disk_names.append(disk_name)

        return disk_names

    # ------------------------------------------  "get_attributes" Function  -------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def get_attributes(self):
        """
        DOCSTRING : this function is to get some smart attributes of all disks
        Args : ---
        Returns : a dictionary has all disks names as a key , and the value of each key will be represented as
                    dictionary of smart attributes names as a key and each attribute raw value as a value ...
                { disk1 : {attr1:val1 , attr2:val2 , attr3:val3} , disk2 : {attr1:val1 , attr2:val2 , attr3:val3} , ...}
        """

        __smart_attributes = {}

        try:
            # Get all Disks :
            # ===============
            all_disk_names = self.get_disk_list()

            # Loop on all disks to get SMART attributes for each one :
            # ========================================================
            metric_values = {}

            for disk_name in all_disk_names:
                output, err = exec_command("smartctl -A /dev/{}".format(disk_name))

                for line in output.splitlines():
                    if "Pre-fail" in line or "Old_age" in line:
                        fields = line.split()

                        # Get RAW_VALUE of : Reallocated_Sector_Ct --> ID = 5 :
                        # -----------------------------------------------------
                        if fields[0] == "5":
                            if fields[9].isdigit():
                                metric_values['reallocated_sector_ct'] = int(fields[9])
                            else:
                                metric_values['reallocated_sector_ct'] = int(re.search(r'\d+', fields[9]).group())

                        # Get RAW_VALUE of : Power_On_Hours --> ID = 9 :
                        # ----------------------------------------------
                        elif fields[0] == "9":
                            if fields[9].isdigit():
                                metric_values['power_on_hours'] = int(fields[9])
                            else:
                                metric_values['power_on_hours'] = int(re.search(r'\d+', fields[9]).group())

                        # Get RAW_VALUE of : Temperature_Celsius --> ID = 194 :
                        # -----------------------------------------------------
                        elif fields[0] == "194":
                            if fields[9].isdigit():
                                metric_values['temperature_celsius'] = int(fields[9])
                            else:
                                metric_values['temperature_celsius'] = int(re.search(r'\d+', fields[9]).group())

                __smart_attributes[disk_name] = metric_values
                metric_values = {}

        except:
            pass

        return __smart_attributes

    # ----------------------------------------  "get_overall_health" Function  -----------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    def get_overall_health(self):
        """
        DOCSTRING : this function is to get the overall_health of all disks
        Args : ---
        Returns : a dictionary has all disks names as a key , and the value of each disk overall_health ...
                { disk1 : overall_health1 , disk2 : overall_health2 , ...}
        """
        __overall_health = {}

        try:
            # Get all Disks :
            # ===============
            all_disk_names = self.get_disk_list()

            # Loop on all disks to get SMART overall-health for each one :
            # ============================================================
            for disk_name in all_disk_names:
                output, err = exec_command("smartctl -H /dev/{}".format(disk_name))

                # Getting one of the words : PASSED , FAILED , UNKNOWN
                health_result = re.findall(r"(?<=SMART overall-health self-assessment test result: )(\w+)", output)
                if not health_result:
                    health_result = re.findall(r"(?<=SMART Health Status: )(\w+)", output)
                    if not health_result:
                        continue

                # Checks on health_result :
                if ('FAILED' in health_result[0]) or ('NOT' in health_result[0]):
                    health_result[0] = 'Failed'

                elif ('PASSED' in health_result[0]) or ('OK' in health_result[0]):
                    health_result[0] = 'Passed'

                elif 'UNKNOWN' in health_result[0]:
                    health_result[0] = 'Unknown'

                __overall_health[disk_name] = health_result[0]

        except:
            pass

        return __overall_health
