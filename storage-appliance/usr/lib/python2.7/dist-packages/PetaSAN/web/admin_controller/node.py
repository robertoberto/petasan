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

from PetaSAN.backend.replication.manage_users import ManageUsers
from flask import Blueprint, render_template, request, redirect, url_for, session
import sys

from PetaSAN.backend.manage_node import *
from PetaSAN.core.security.basic_auth import requires_auth, authorization

reload(sys)
sys.setdefaultencoding('utf8')

node_controller = Blueprint('node_controller', __name__)


########################################################################################################################
@node_controller.route('/node/list/disk_list/<node_name>', defaults={'process_id': 0}, methods=['GET'])
@node_controller.route('/node/list/disk_list/<node_name>/<process_id>', methods=['GET'])
@requires_auth
@authorization("NodeList")
def disk_list(node_name, process_id):
    mesg_err = ""
    mesg_success = ""
    mesg_warning = ""
    node_name_val = None
    try:
        node_name_val = node_name
        process_id_val = process_id
        manage_node = ManageNode()
        node_info = manage_node.get_node_info(node_name)
        node_storage_role = node_info.is_storage
        if "err" in session:
            mesg_err = session["err"]
            session.pop("err")
        elif "success" in session:
            mesg_success = session["success"]
            session.pop("success")
        elif "warning" in session:
            mesg_warning = session["warning"]
            session.pop("warning")
    except Exception as e:
        mesg_err = "ui_admin_error_loading_disk_page"
    return render_template('admin/node/disk_list.html', nodeName=node_name_val, processID=process_id_val,
                           node_storage_role=node_storage_role, err=mesg_err,
                           success=mesg_success, warning=mesg_warning)


########################################################################################################################
@node_controller.route('/node/list/get_all_disk/<node_name>/<process_id>', methods=['GET'])
@requires_auth
@authorization("NodeList")
def get_all_disk(node_name, process_id):
    if request.method == 'GET':
        nodes = ManageNode()
        disk_ls = nodes.get_disk_list(node_name, process_id)
        json_data = json.dumps([obj.__dict__ for obj in disk_ls])
        return json_data


########################################################################################################################
@node_controller.route('/node/list')
@requires_auth
@authorization("NodeList")
def node_list():
    nodes = ManageNode()
    node_status = NodeStatus()
    node_list = nodes.get_node_list()
    mesg_err = ""
    mesg_success = ""
    mesg_warning = ""

    try:
        if "err" in session:
            mesg_err = session["err"]
            session.pop("err")
        elif "success" in session:
            mesg_success = session["success"]
            session.pop("success")
        elif "warning" in session:
            mesg_warning = session["warning"]
            session.pop("warning")

        return render_template('admin/node/node_list.html', nodeList=node_list, nodeStatus=node_status, err=mesg_err,
                               success=mesg_success, warning=mesg_warning)

    except Exception as e:
        mesg_err = "ui_admin_error_loading_node_page"
        return render_template('admin/node/node_list.html', err=mesg_err)


########################################################################################################################
@node_controller.route('/node/list/delete_node/<node_name>', methods=['POST'])
@requires_auth
@authorization("NodeList")
def remove_node(node_name):
    if request.method == 'POST':
        manage_node = ManageNode()
        status = manage_node.delete_node(node_name)
        delete_status = DeleteNodeStatus()
        if (status == True):
            session['success'] = "ui_admin_delete_node_success"
        elif (status == delete_status.not_allow):
            session['warning'] = "ui_admin_delete_node_validation"
        else:
            session['err'] = "ui_admin_delete_node_fail"

        return redirect(url_for('node_controller.node_list'))


########################################################################################################################
@node_controller.route('/node/<node_name>/manage_roles', methods=['GET'])
@requires_auth
@authorization("NodeList")
def node_manage_roles(node_name):
    mesg_err = ""
    mesg_success = ""
    mesg_warning = ""
    try:
        if "err" in session:
            mesg_err = session["err"]
            session.pop("err")
            manage_node = ManageNode()
            node_info = manage_node.get_node_info(node_name)
            return render_template('admin/node/manage_roles.html', node=node_info, err=mesg_err)
        elif "success" in session:
            mesg_success = session["success"]
            session.pop("success")
            manage_node = ManageNode()
            node_info = manage_node.get_node_info(node_name)
            return render_template('admin/node/manage_roles.html', node=node_info, success=mesg_success)
        elif "warning" in session:
            mesg_warning = session["warning"]
            session.pop("warning")
            manage_node = ManageNode()
            node_info = manage_node.get_node_info(node_name)
            return render_template('admin/node/manage_roles.html', node=node_info, warning=mesg_warning)
        else:
            manage_node = ManageNode()
            node_info = manage_node.get_node_info(node_name)
            return render_template('admin/node/manage_roles.html', node=node_info)

    except Exception as e:
        mesg_err = "ui_node_update_node_role_exep"
        return render_template('admin/node/node_list.html', err=mesg_err)


########################################################################################################################
@node_controller.route('/node/<node_name>/manage_roles/update', methods=['POST'])
@requires_auth
@authorization("NodeList")
def update_node_manage_roles(node_name):
    try:
        try:
            if request.form['option_iscsi'] == 'iscsi':
                is_iscsi = 1
        except Exception as ex:
            is_iscsi = 0
            logger.error(ex)
        try:
            if request.form['option_storage'] == 'storage':
                is_storage = 1
        except Exception as ex:
            is_storage = 0
            logger.error(ex)
        try:
            if request.form['backup'] == 'backup_node':
                is_backup = 1
        except Exception as ex:
            is_backup = 0
            logger.error(ex)
        manage_node = ManageNode()
        try:
            manage_node.update_node_role(node_name, is_storage, is_iscsi, is_backup)
            manage_users = ManageUsers()
            stat = manage_users.sync_users(node_name)
            session['success'] = "ui_node_update_node_role_succ"
            return redirect(url_for('node_controller.node_list'))

        except Exception as ex:
            session['err'] = "ui_node_update_node_role_err"
            return redirect(url_for('node_controller.node_manage_roles', node_name=node_name))

    except Exception as e:
        session['err'] = "ui_node_update_node_role_exep"
        return redirect(url_for('node_controller.node_manage_roles', node_name=node_name), 307)


########################################################################################################################
@node_controller.route('/node/<node_name>/show_log', methods=['POST', 'GET'])
@requires_auth
@authorization("NodeList")
def node_show_log(node_name):
    mesg_err = ""
    mesg_success = ""
    mesg_warning = ""
    logs = []
    try:
        if "err" in session:
            mesg_err = session["err"]
            session.pop("err")
            manage_node = ManageNode()
            node_log = manage_node.get_node_log(node_name)
            lines = node_log.split("\n")
            for line in reversed(lines):
                logs.append(line)
            return render_template('admin/node/show_log.html', node_name=node_name, err=mesg_err, logs=logs)
        elif "success" in session:
            mesg_success = session["success"]
            session.pop("success")
            manage_node = ManageNode()
            node_log = manage_node.get_node_log(node_name)
            lines = node_log.split("\n")
            for line in reversed(lines):
                logs.append(line)
            return render_template('admin/node/show_log.html', node_name=node_name, success=mesg_success, logs=logs)
        elif "warning" in session:
            mesg_warning = session["warning"]
            session.pop("warning")
            manage_node = ManageNode()
            node_log = manage_node.get_node_log(node_name)
            lines = node_log.split("\n")
            for line in reversed(lines):
                logs.append(line)
            return render_template('admin/node/show_log.html', node_name=node_name, warning=mesg_warning, logs=logs)
        else:
            manage_node = ManageNode()
            node_log = manage_node.get_node_log(node_name)
            lines = node_log.split("\n")
            for line in reversed(lines):
                logs.append(line)
            return render_template('admin/node/show_log.html', node_name=node_name, logs=logs)

    except Exception as e:
        session['err'] = "ui_node_show_node_log_exep"
        return redirect(url_for('node_controller.node_list'))


########################################################################################################################
@node_controller.route('/node/<node_name>/show_log/refresh', methods=['GET'])
@requires_auth
@authorization("NodeList")
def refresh_show_log(node_name):
    return redirect(url_for('node_controller.node_show_log', node_name=node_name))


########################################################################################################################
@node_controller.route('/node/<node_name>/disk_list/add_osd/<disk_name>', methods=['POST'])
@requires_auth
@authorization("NodeList")
def add_osd(node_name, disk_name):
    print("--------------------------------------------------")
    print("Adding OSD")
    print("----------")
    print("node_name = {}".format(node_name))
    print("disk_name = {}".format(disk_name))
    print("--------------------------------------------------")
    try:
        manage_node = ManageNode()
        pid = manage_node.add_osd(node_name, disk_name)
        if pid.strip() != '-1':
            # session['success'] = "ui_node_add_osd_succ"
            return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))
        elif pid.strip() == '-1':
            session['err'] = "ui_node_add_osd_err"
            return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

    except Exception as e:
        session['err'] = "ui_node_add_osd_exep"
        return redirect(url_for('node_controller.disk_list', node_name=node_name))


########################################################################################################################
@node_controller.route('/node/<node_name>/disk_list/delete_osd/<disk_name>/<osd_id>', methods=['POST'])
@requires_auth
@authorization("NodeList")
def delete_osd(node_name, disk_name, osd_id):
    try:
        manage_node = ManageNode()
        try:
            pid = manage_node.delete_osd(node_name, disk_name, osd_id)
            if pid.strip() != '-1':
                # session['success'] = "Disk deleted successfully"
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))
            elif pid.strip() == '-1':
                session['err'] = "ui_node_delete_osd_err"
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

        except Exception as e:
            session['err'] = "ui_node_delete_osd_err"
            return redirect(url_for('node_controller.disk_list', node_name=node_name))

    except Exception as e:
        session['err'] = "ui_node_delete_osd_exep"
        return redirect(url_for('node_controller.disk_list', node_name=node_name))


########################################################################################################################
@node_controller.route('/node/<node_name>/disk_list/add_journal/<disk_name>', methods=['POST'])
@requires_auth
@authorization("NodeList")
def add_journal(node_name, disk_name):
    print("--------------------------------------------------")
    print("Adding Journal")
    print("--------------")
    print("node_name = {}".format(node_name))
    print("disk_name = {}".format(disk_name))
    print("--------------------------------------------------")
    try:
        manage_node = ManageNode()
        pid = manage_node.add_journal(node_name, disk_name)

        if pid.strip() > '-1':
            # session['success'] = "ui_node_add_journal_succ"
            return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))
        elif pid.strip() == '-1':
            session['err'] = "ui_system_cannot_add_journal_err"
            return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

    except Exception as e:
        session['err'] = "ui_system_cannot_add_journal_exep"
        return redirect(url_for('node_controller.disk_list', node_name=node_name))


########################################################################################################################
@node_controller.route('/node/<node_name>/disk_list/delete_journal/<disk_name>', methods=['POST'])
@requires_auth
@authorization("NodeList")
def delete_journal(node_name, disk_name):
    try:
        manage_node = ManageNode()
        try:
            pid = manage_node.delete_journal(node_name, disk_name)
            if pid.strip() != '-1':
                # session['success'] = "Disk deleted successfully"
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))
            elif pid.strip() == '-1':
                session['err'] = "ui_node_delete_journal_err"
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

        except Exception as e:
            session['err'] = "ui_node_delete_journal_err"
            return redirect(url_for('node_controller.disk_list', node_name=node_name))

    except Exception as e:
        session['err'] = "ui_node_delete_journal_exc"
        return redirect(url_for('node_controller.disk_list', node_name=node_name))


########################################################################################################################
@node_controller.route('/node/<node_name>/disk_list/delete_cache/<disk_name>', methods=['POST'])
@requires_auth
@authorization("NodeList")
def delete_cache(node_name, disk_name):
    try:
        manage_node = ManageNode()
        try:
            pid = manage_node.delete_cache(node_name, disk_name)
            if pid.strip() != '-1':
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))
            elif pid.strip() == '-1':
                session['err'] = "ui_node_delete_cache_err"
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

        except Exception as e:
            session['err'] = "ui_node_delete_cache_err"
            return redirect(url_for('node_controller.disk_list', node_name=node_name))

    except Exception as e:
        session['err'] = "ui_node_delete_cache_exc"
        return redirect(url_for('node_controller.disk_list', node_name=node_name))


########################################################################################################################

@node_controller.route('/node/<node_name>/disk_list/add_osd_with_journal/<disk_name>', methods=['POST'])
@requires_auth
@authorization("NodeList")
def add_osd_with_journal(node_name, disk_name):
    if request.method == 'POST':
        print("--------------------------------------------------")
        print("Adding OSD with Journal")
        print("-----------------------")
        print("node_name = {}".format(node_name))
        print("disk_name = {}".format(disk_name))
        print("--------------------------------------------------")

        try:
            journal_disk_name = ""
            if request.form["external_journal"] == 'enabled':
                journal_disk_name = request.form["journal_disk_name"]

            print("journal_disk_name = {}".format(journal_disk_name))
            print("--------------------------------------------------")

            manage_node = ManageNode()
            pid = manage_node.add_osd(node_name, disk_name, journal=journal_disk_name)

            if pid.strip() > '-1':
                # session['success'] = "ui_node_add_osd_succ"
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))
            elif pid.strip() == '-1':
                session['err'] = "ui_node_add_osd_err"
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

        except DiskException as e:
            if e.id == DiskException.JOURNAL_NO_SPACE:
                session['err'] = "ui_system_no_journal_space_excep"
            elif e.id == DiskException.JOURNALS_NO_SPACE:
                session['err'] = "ui_system_no_journal_space_excep_all"
            return redirect(url_for('node_controller.disk_list', node_name=node_name))

        except Exception as e:
            session['err'] = "ui_node_add_osd_exep"
            return redirect(url_for('node_controller.disk_list', node_name=node_name))

    return redirect(url_for('node_controller.disk_list', node_name=node_name))


########################################################################################################################
@node_controller.route('/node/<node_name>/disk_list/add_cache/<disk_name>', methods=['POST'])
@requires_auth
@authorization("NodeList")
def add_cache(node_name, disk_name):
    if request.method == 'POST':
        print("--------------------------------------------------")
        print("Adding Cache")
        print("------------")
        print("node_name = {}".format(node_name))
        print("disk_name = {}".format(disk_name))
        print("--------------------------------------------------")

        try:
            partitions = request.form["partitions"]
            print("partitions = {}".format(partitions))
            print("--------------------------------------------------")

            manage_node = ManageNode()
            pid = manage_node.add_cache(node_name, disk_name, partitions)

            if pid.strip() > '-1':
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

            elif pid.strip() == '-1':
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

        except Exception as e:
            #session['err'] = "ui_system_cannot_add_cache_exep"
            return redirect(url_for('node_controller.disk_list', node_name=node_name))

    return redirect(url_for('node_controller.disk_list', node_name=node_name))

########################################################################################################################
@node_controller.route('/node/<node_name>/disk_list/add_osd_with_cache/<disk_name>', methods=['POST'])
@requires_auth
@authorization("NodeList")
def add_osd_with_cache(node_name, disk_name):
    print("--------------------------------------------------")
    print("Adding OSD with Cache")
    print("---------------------")
    print("node_name = {}".format(node_name))
    print("disk_name = {}".format(disk_name))
    print("--------------------------------------------------")

    if request.method == 'POST':
        try:
            cache_type = request.form["external_cache"]
            cache = request.form["cache_disk_name"]
            print("cache_type = {}".format(cache_type))
            print("cache = {}".format(cache))
            print("--------------------------------------------------")

            manage_node = ManageNode()
            pid = manage_node.add_osd(node_name, disk_name, journal=None, cache=cache, cache_type=cache_type)

            if pid.strip() > '-1':
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

            elif pid.strip() == '-1':
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

        except DiskException as e:
            if e.id == DiskException.CACHE_NO_SPACE:
                session['err'] = "ui_system_no_cache_space_excep"
            return redirect(url_for('node_controller.disk_list', node_name=node_name))

        except Exception as e:
            return redirect(url_for('node_controller.disk_list', node_name=node_name))

    return redirect(url_for('node_controller.disk_list', node_name=node_name))

########################################################################################################################
@node_controller.route('/node/<node_name>/disk_list/add_osd_with_journal_cache/<disk_name>', methods=['POST'])
@requires_auth
@authorization("NodeList")
def add_osd_with_journal_cache(node_name, disk_name):
    if request.method == 'POST':
        print("--------------------------------------------------")
        print("Adding OSD with Cache & Journal")
        print("-------------------------------")
        print("node_name = {}".format(node_name))
        print("disk_name = {}".format(disk_name))
        print("--------------------------------------------------")

        try:
            # Get Journal #
            journal_disk_name = ""
            if request.form["external_journal"] == 'enabled':
                journal_disk_name = request.form["journal_disk_name"]

            print("journal_disk_name = {}".format(journal_disk_name))
            print("--------------------------------------------------")

            # Get Cache #
            cache_type = request.form["external_cache"]
            cache = request.form["cache_disk_name"]
            print("cache_type = {}".format(cache_type))
            print("cache = {}".format(cache))
            print("--------------------------------------------------")

            manage_node = ManageNode()
            pid = manage_node.add_osd(node_name,
                                      disk_name,
                                      journal=journal_disk_name,
                                      cache=cache,
                                      cache_type=cache_type)

            if pid.strip() > '-1':
                # session['success'] = "ui_node_add_osd_succ"
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))
            elif pid.strip() == '-1':
                session['err'] = "ui_node_add_osd_err"
                return redirect(url_for('node_controller.disk_list', node_name=node_name, process_id=pid.strip()))

        except DiskException as e:
            if e.id == DiskException.JOURNAL_NO_SPACE:
                session['err'] = "ui_system_no_journal_space_excep"

            elif e.id == DiskException.JOURNALS_NO_SPACE:
                session['err'] = "ui_system_no_journal_space_excep_all"

            elif e.id == DiskException.CACHE_NO_SPACE:
                session['err'] = "ui_system_no_cache_space_excep"

            return redirect(url_for('node_controller.disk_list', node_name=node_name))

        except Exception:
            session['err'] = "ui_node_add_osd_exep"
            return redirect(url_for('node_controller.disk_list', node_name=node_name))

    return redirect(url_for('node_controller.disk_list', node_name=node_name))


########################################################################################################################
