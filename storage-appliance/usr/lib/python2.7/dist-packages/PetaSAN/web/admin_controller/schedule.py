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

import json
from flask import Blueprint, render_template, request, redirect, url_for, session

from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.core.common.log import logger

schedule_controller = Blueprint('schedule_controller', __name__)


list_err = "err"
list_warning = "warning"
list_success = "success"


# @schedule_controller.route('/schedule/open/<types>', methods=['GET', 'POST'])
# @requires_auth
# def open_schedule(types):
#     return render_template('admin/schedule/view_schedule.html' , types = types)
