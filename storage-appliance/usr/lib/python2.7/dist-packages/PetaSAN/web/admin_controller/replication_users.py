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

from PetaSAN.core.common.CustomException import CephException, ReplicationException
from flask import Blueprint, render_template, request, redirect, url_for, session
from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.backend.replication.manage_users import ManageUsers
from PetaSAN.backend.manage_pools import ManagePools
from PetaSAN.core.common.log import logger
import json
from PetaSAN.core.common.CustomException import ConsulException

replication_users_controller = Blueprint('replication_users_controller', __name__)

list_err = "err"
list_warning = "warning"
list_success = "success"


@replication_users_controller.route('/replication_users/users_list', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationUsers')
def users_list():
    if request.method == 'GET' or request.method == 'POST':
        users_list = []
        message = "ui_admin_replication_user_info_message"
        try:
            users_list = ManageUsers().get_replication_users()
            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/cluster_users/users_list.html', users_list=users_list, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('/admin/replication/cluster_users/users_list.html', users_list=users_list, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('/admin/replication/cluster_users/users_list.html', users_list=users_list, warning=result)

            else:
                return render_template('/admin/replication/cluster_users/users_list.html',info=message, users_list=users_list)

        except ConsulException as e:
            logger.error(e)

        except Exception as e:
            logger.error(e)

        return render_template('/admin/replication/cluster_users/users_list.html',info=message, users_list= users_list)





@replication_users_controller.route('/replication_users/add_user', methods=['GET', 'POST'])
@replication_users_controller.route('/replication_users/add_user/<name>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationUsers')
def add_rep_usr(name = ""):
    if request.method == 'GET' or request.method == 'POST':
        try:
            manage_pools = ManagePools()
            active_pools = manage_pools.get_active_pools()
            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/cluster_users/add_user.html',name = name,active_pools = active_pools, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('/admin/replication/cluster_users/add_user.html',name = name,active_pools = active_pools, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('/admin/replication/cluster_users/add_user.html',name = name,active_pools = active_pools, warning=result)

            else:

                return render_template('/admin/replication/cluster_users/add_user.html',active_pools = active_pools,name = name)

        except ConsulException as e:
            logger.error(e)

        except Exception as e:
            logger.error(e)

        return render_template('/admin/replication/cluster_users/add_user.html',active_pools = active_pools,name = name)




@replication_users_controller.route('/replication_users/remove_user/<name>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationUsers')
def remove_user(name):
    try:
        stat = ManageUsers().delete_replication_user(name)
        if stat:
            session['success'] = "ui_admin_delete_rep_user_success"
        else:
            session['err'] = "ui_admin_delete_rep_user_fail"

        return redirect(url_for('replication_users_controller.users_list'))

    except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)

    except ConsulException as e:
            logger.error(e)

    except Exception as e:
        logger.error(e)

    session['err'] = "ui_admin_delete_rep_user_fail"
    return redirect(url_for('replication_users_controller.users_list'))



@replication_users_controller.route('/replication_users/edit_user/<name>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationUsers')
def edit_user(name):
    auth_pools = []
    active_pools = []
    user_info = ""
    if request.method == 'GET' or request.method == 'POST':
        try:
            user_info = ManageUsers().get_replication_user(name)
            manage_pools = ManagePools()
            active_pools = manage_pools.get_active_pools()
            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/cluster_users/edit_user.html',user_info = user_info,active_pools = active_pools, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('/admin/replication/cluster_users/edit_user.html',user_info = user_info,active_pools = active_pools, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('/admin/replication/cluster_users/edit_user.html',user_info = user_info,active_pools = active_pools, warning=result)

            else:
                return render_template('/admin/replication/cluster_users/edit_user.html',active_pools = active_pools,user_info = user_info)

        except ConsulException as e:
            logger.error(e)

        except Exception as e:
            logger.error(e)

        return render_template('/admin/replication/cluster_users/edit_user.html',active_pools = active_pools,user_info = user_info)



@replication_users_controller.route('/replication_users/update_user_private_key/<user_name>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationUsers')
def reset_private_key(user_name):
    try:
        if request.method == 'GET' or request.method == 'POST':
            private_key = ManageUsers().reset_prv_key(user_name)
            return json.dumps(private_key)
    except ConsulException as e:
        logger.error(e)



@replication_users_controller.route('/replication_users/get_user/<user_name>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationUsers')
def get_user_details(user_name):
    if request.method == 'GET' or request.method == 'POST':
        user = ManageUsers().get_replication_user(user_name)
        user_dict = user.__dict__
        return json.dumps(user_dict)



@replication_users_controller.route('/replication_users/save_user', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationUsers')
def save_user():
    if request.method == 'POST':
        name = ""
        active_pools = []
        try:
            name = request.form['userName']
            auth_pools = request.form.getlist('pools[]')
            manage_pools = ManagePools()
            active_pools = manage_pools.get_active_pools()
            ManageUsers().add_user(name, auth_pools)

            user_info = ManageUsers().get_replication_user(name)
            session['success'] = "ui_admin_add_rep_user_success"
            result = session['success']
            session.pop("success")
            return render_template('/admin/replication/cluster_users/edit_user.html',active_pools = active_pools ,user_info=user_info, success = result)

        except ReplicationException as e:
            if e.id == ReplicationException.CEPH_USER_EXIST or e.id == ReplicationException.SYSTEM_USER_EXIST:
                session['err'] = "ui_admin_add_rep_user_already_exist"
                logger.error(e)
                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/cluster_users/add_user.html',name = name, err=result, active_pools = active_pools)
            elif e.id == ReplicationException.NOT_BACKUP_NODE:
                session['err'] = "ui_admin_no_backup_node"
                logger.error(e)
                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/cluster_users/add_user.html',name = name, err=result, active_pools = active_pools)
            elif e.id == ReplicationException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_error_adding_user"
                logger.error(e)
                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/cluster_users/add_user.html',name = name, err=result, active_pools = active_pools)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            result = session["err"]
            session.pop("err")
            return render_template('/admin/replication/cluster_users/add_user.html',name = name, err=result, active_pools = active_pools)

        except ConsulException as e:
            logger.error(e)

        except Exception as e:
            logger.error(e)

        session['err'] = "ui_admin_error_adding_user"
        result = session["err"]
        session.pop("err")
        return render_template('/admin/replication/cluster_users/add_user.html', name = name,err=result, active_pools = active_pools)





@replication_users_controller.route('/replication_users/update_user/<user_name>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationUsers')
def update_user(user_name):
    if request.method == 'GET' or request.method == 'POST':
        try:
            auth_pools = request.form.getlist('pools[]')
            manage_users = ManageUsers()
            status = manage_users.update_auth_pools(user_name, auth_pools)
            manage_pools = ManagePools()
            active_pools = manage_pools.get_active_pools()
            user_info = manage_users.get_replication_user(user_name)
            if not status:
                session['err'] = "ui_admin_error_updating_authorized_pools"
                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/cluster_users/edit_user.html',active_pools = active_pools ,user_info = user_info, err = result)

            session['success'] = "ui_admin_update_authorized_pools_success"
            result = session['success']
            session.pop("success")
            return render_template('/admin/replication/cluster_users/edit_user.html',active_pools = active_pools,user_info = user_info, success = result)

        except ReplicationException as e:
            logger.error(e)
            session['err'] = "ui_admin_error_updating_authorized_pools"
            result = session["err"]
            session.pop("err")
            return render_template('/admin/replication/cluster_users/edit_user.html',active_pools = active_pools ,user_info = user_info, err = result)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            result = session["err"]
            session.pop("err")
            return render_template('/admin/replication/cluster_users/edit_user.html',active_pools = active_pools,user_info = user_info, err = result)

        except ConsulException as e:
            logger.error(e)

        except Exception as e:
            logger.error(e)

        session['err'] = "ui_admin_error_updating_authorized_pools"
        result = session["err"]
        session.pop("err")
        return render_template('/admin/replication/cluster_users/edit_user.html',active_pools = active_pools ,user_info = user_info, err = result)


