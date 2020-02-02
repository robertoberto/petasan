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
from PetaSAN.core.security.basic_auth import requires_auth,authorization
from PetaSAN.backend.manage_security import ManageUser
from PetaSAN.core.entity.user_info import User
from flask import Blueprint, render_template, request, redirect, url_for, session
from PetaSAN.core.entity.models.user import AddUserForm,change_password_form

from PetaSAN.core.common.enums import ManageUserStatus
from PetaSAN.core.common.log import logger
user_controller = Blueprint('user_controller', __name__)
list_err= "err"
list_warning="warning"
list_success="success"

# load add user form
@user_controller.route('/user/add',methods=['POST','GET'])
@requires_auth
@authorization("AddUser")
def add_user():
     if request.method == 'GET' or request.method == 'POST':
         user_name = session['user']
         manage_user = ManageUser()
         user_roles = manage_user.get_roles()
         result=""
         if list_err in session :

              result=session[list_err]
              session.pop(list_err)
              return render_template('admin/user/add_user.html',err=result,roles=user_roles, form =request.form)
         elif list_warning in session :
             result=session[list_warning]
             session.pop(list_warning)
             return render_template('admin/user/add_user.html',warning=result,roles=user_roles, form =request.form)
         elif list_success in session :
             result=session[list_success]
             session.pop(list_success)
             return render_template('admin/user/add_user.html',success=result,roles=user_roles, form =request.form)
         else:
             form1= AddUserForm()
             return render_template('admin/user/add_user.html',roles=user_roles, form =form1)

# add user
@user_controller.route('/user/add/save', methods=['POST'])
@requires_auth
@authorization("AddUser")
def save_user():
    if request.method == 'POST':
        try :
            user = User()
            user.name = request.form['name']
            user.user_name = request.form['userName']
            user.role_id = int(request.form['role'])
            user.password = request.form['userPassword']
            user.email = str(request.form['email'])
            try:
                if request.form['notify_mail'] == 'Notify':
                    user.notfiy = True
            except Exception as ex:
                    user.notfiy=False
                    logger.error("notify err")
            manage_user = ManageUser()
            status = manage_user.add_user(user)
            if status==ManageUserStatus.done :
                  session['success']="ui_admin_add_user_suc"
                  return redirect(url_for('user_controller.user_list'))
            elif status == ManageUserStatus.exists :
                 session['err']="ui_admin_add_user_err_exists"
                 return redirect(url_for('user_controller.add_user'),307)
            elif status == ManageUserStatus.error :
                 session['err']="ui_admin_add_user_err"
                 return redirect(url_for('user_controller.add_user'),307)
        except Exception as e:
                 session['err']="ui_admin_add_user_err_exception"
                 logger.error(e)
                 return redirect(url_for('user_controller.add_user'),307)

# load edit user form
@user_controller.route('/user/list/edit/<user_id>',methods=['POST','GET'])
@requires_auth
@authorization("UserList")
def edit_user(user_id):
    if request.method == 'GET' or request.method == 'POST':
        manage_user = ManageUser();
        selected_user = manage_user.get_user(user_id)
        user_roles = manage_user.get_roles()
        return render_template('admin/user/edit_user.html',roles=user_roles,user=selected_user)

# edit user
@user_controller.route('/user/edit/save', methods=['POST'])
@requires_auth
@authorization("UserList")
def save_edit_user():
    if request.method == 'POST':
        try :
            user = User()
            user.name = request.form['name']
            user.user_name = request.form['userName']
            user.role_id = int(request.form['role'])
            user.password = request.form['userPassword']
            user.email = str(request.form['email'])
            try:
                if request.form["notify_mail"] == "Notify":
                    user.notfiy=True
            except Exception as e:
                    user.notfiy=False
            manage_user = ManageUser()
            status = manage_user.update_user(user)
            if status==ManageUserStatus.done :
                  session['success']="ui_admin_edit_user_suc"
                  return redirect(url_for('user_controller.user_list'))
            elif status == ManageUserStatus.not_exists :
                 session['err']="ui_admin_edit_user_err_not_exists"
                 return redirect(url_for('user_controller.edit_user',user_id=user.user_name),307)
            elif status == ManageUserStatus.error :
                 session['err']="ui_admin_edit_user_err"
                 return redirect(url_for('user_controller.edit_user',user_id=user.user_name),307)
        except Exception as e:
            session['err']="ui_admin_edit_user_err_exception"
            logger.error(e)
            return redirect(url_for('user_controller.edit_user',user_id=user.user_name),307)

#load change password form
@user_controller.route('/user/changePassword',methods=['POST','GET'])
@requires_auth
def change_password():
     if request.method == 'GET' or request.method == 'POST':
         result=""
         if list_err in session :
              result=session[list_err]
              session.pop(list_err)
              return render_template('admin/user/change_password.html',err=result, form =request.form)
         elif list_warning in session :
             result=session[list_warning]
             session.pop(list_warning)
             return render_template('admin/user/change_password.html',warning=result, form =request.form)
         elif list_success in session :
             result=session[list_success]
             session.pop(list_success)
             return render_template('admin/user/change_password.html',success=result, form =request.form)
         else:
             return render_template('admin/user/change_password.html')

#change password
@user_controller.route('/user/changePassword/save', methods=['POST'])
@requires_auth
def save_change_password():
    if request.method == 'POST':
        try :
            user_name = session['user']
            user_password = request.form['newPassword']
            manage_user = ManageUser()
            status = manage_user.update_password(user_name,user_password)
            if status==ManageUserStatus.done :
                  # session['success']="Password updated successfully ."
                  return redirect('/')
                  return redirect(url_for('user_controller.change_password'))
            elif status == ManageUserStatus.not_exists :
                 session['err']="ui_admin_change_password_err_not_exists"
                 return redirect(url_for('user_controller.change_password'),307)
            elif status == ManageUserStatus.error :
                 session['err']="ui_admin_change_password_err"
                 return redirect(url_for('user_controller.change_password'),307)
        except Exception as e:
                 session['err']="ui_admin_change_password_err_exception"
                 logger.error(e)
                 return redirect(url_for('user_controller.change_password'),307)


@user_controller.route('/user/list')
@requires_auth
@authorization("UserList")
def user_list():
    mesg_err=""
    mesg_success=""
    mesg_warning=""
    available_user_list=None
    user_roles = None
    user_name = session['user']
    try:
        manage_user = ManageUser()
        available_user_list = manage_user.get_users()
        user_roles = manage_user.get_roles()
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
        mesg_err="error in loading page"

    return render_template('admin/user/list.html', user_list=available_user_list, user_roles=user_roles,
                           err=mesg_err,success=mesg_success, warning=mesg_warning)


@user_controller.route('/user/list/remove/<user_id>', methods=['GET','POST'])
@requires_auth
@authorization("UserList")
def remove_user(user_id):
     if request.method == 'GET' or request.method == 'POST':
        manage_user = ManageUser()
        status = manage_user.delete_user(user_id)
        if(status == ManageUserStatus.done):
            session['success'] = "ui_admin_remove_user_suc"
        else:
            session['err'] = "ui_admin_remove_user_err"

        return redirect(url_for('user_controller.user_list'))


@user_controller.route('/user/<user_id>')
@requires_auth
@authorization("UserList")
def get_selected_user_info(user_id):
        manage_user = ManageUser();
        selected_user = manage_user.get_user(user_id)

        json_data = json.dumps(selected_user.__dict__, sort_keys=True)
        return json_data
