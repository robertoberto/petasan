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




def get_next_id(list, length):
    if not list:
        list=["0"]
    max_id = max(list)
    next_id = int(max_id) + 1
    remain_digit = 0
    actual_length = len(str(next_id))
    if actual_length < length:
        remain_digit = length - actual_length
    next_id_as_str = ""
    if remain_digit > 0:
        for i in range(remain_digit):
            next_id_as_str += "0"
    next_id_as_str += str(next_id)
    return next_id_as_str
