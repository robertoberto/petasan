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

from PetaSAN.core.common.messages import gettext
from PetaSAN.core.entity.authorize import Page
from PetaSAN.core.security.api import RoleAPI, UserAPI
from PetaSAN.core.security.api import PageAPI


from functools import update_wrapper
from functools import wraps
from flask import g, request, redirect, url_for, Response, sessions, render_template, session,Flask


def check_auth(username, password):
    """
    This function is called to check if a username / password combination is valid.
    """
    user_api = UserAPI()
    user = user_api.get_user(str(username).lower())
    if user and user.user_name == str(username).lower() and user.password == password:
        session['user'] = user.user_name
        session['role_id']= user.role_id
        return True
    return False


def authenticate():
    """Sends a 401 response to enable basic auth"""
    return render_template('admin/login.html')


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        status = -1
        if 'sid' in session:
            if session['sid'] == "-1":
                return render_template('admin/login.html', err=gettext("ui_admin_login_consul_connection_error"))
        else:
            return render_template('admin/login.html', err=gettext("ui_admin_login_consul_connection_error"))
        if 'user' in session:
            status = 1
        elif status == -1:
            try:
                if request.url_rule.rule == '/':
                    username = request.form["username"]
                    password = request.form["password"]
                else:
                    return render_template('admin/login.html')
            except Exception as e:
                return render_template('admin/login.html')
            if (username and password and check_auth(username, password)):
                status = 1
            else:
                return render_template('admin/login.html', err="Incorrect username or password. Please try again.")

        if status == 1:
            return f(*args, **kwargs)
        else:
            return authenticate()

    return decorated

def authorization(page_name):

    def decorator(fn):
        def wrapped_function(*args, **kwargs):
            if not 'user' in session:
                return render_template('admin/login.html')
            page_api= PageAPI()
            role_api = RoleAPI()
            page = Page()
            page= page_api.get_page(page_name)
            if page:
               if not role_api.is_page_allowed(page.id,session['role_id']):
                    return redirect('/403')
               else:
                   return fn(*args, **kwargs)
            else:
                return redirect('/403')



        return update_wrapper(wrapped_function, fn)
    return decorator
