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

from flask import Blueprint, render_template, request, session, redirect, url_for
from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.backend.manage_disk import ManageDisk
import json

backup_controller = Blueprint('backup_controller', __name__)


@backup_controller.route('/backup/backup_disk', methods=['GET', 'POST'])
@requires_auth
@authorization('BackupDisk')
def start_backup_disk():

    if request.method == 'GET' or request.method == 'POST':

        #return redirect(url_for('backup_controller.test'))

        if "success" in session:
            result = session["success"]
            session.pop("success")
            return render_template('/admin/backup/backup_disk.html' , success = result)

        return render_template('/admin/backup/backup_disk.html')


@backup_controller.route('/backup/test', methods=['GET', 'POST'])
@requires_auth
@authorization('test')
def test():

    if request.method == 'GET' or request.method == 'POST':


        if "success" in session:
            result = session["success"]
            session.pop("success")

            return render_template('/admin/backup/test_backup.html' , success = result)

        return render_template('/admin/backup/test_backup.html')


@backup_controller.route('/backup/disks', methods=['GET', 'POST'])
@requires_auth
@authorization('BackupDisk')
def get_disks_list():

    if request.method == 'GET' or request.method == 'POST':

        mesg_err = ""
        mesg_success = ""
        mesg_warning = ""
        available_disk_list = []

        try:
            disks = {}
            manage_disk = ManageDisk()
            available_disk_list = manage_disk.get_disks_meta()

            # print("available_disk_list =", len(available_disk_list))
            # print(available_disk_list[0].id)

            if "err" in session:
                mesg_err = session["err"]
                session.pop("err")
            elif "success" in session:
                mesg_success = session["success"]
                session.pop("success")
            elif "warning" in session:
                mesg_warning = session["warning"]
                session.pop("warning")

            # print("start dump")

            x = 1
            for obj in available_disk_list:
                disks[x] = obj.__dict__
                x += 1

            #disks= {"t1": {'id':10, 'name': 'doaa'} , "t2": {'id':20, 'name': 'manar'}}


            json_data = json.dumps(disks)

            # print("after dump")
            # print(json_data)

            return json_data

        except Exception as e:
            mesg_err = "error in loading page"
            return render_template('/admin/backup/disks_list.html', err=mesg_err)

        #return render_template('/admin/backup/disks_list.html', diskList=available_disk_list, err=mesg_err, success=mesg_success, warning=mesg_warning)

