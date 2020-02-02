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
import ast
from PetaSAN.core.common.CustomException import CephException, CrushException
from PetaSAN.backend.manage_crush import ManageCrush
from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.backend.manage_pools import ManagePools
from PetaSAN.core.common.log import logger

crush_controller = Blueprint('crush_controller', __name__)

list_err = "err"
list_warning = "warning"
list_success = "success"


@crush_controller.route('/crush/tree', methods=['GET'])
@requires_auth
@authorization("BucketTree")
def get_bucket_list():
    if request.method == 'GET':
        if list_err in session:
            result = session["err"]
            session.pop("err")
            return render_template('admin/crush/tree.html', err=result)

        elif list_success in session:
            result = session["success"]
            session.pop("success")
            return render_template('admin/crush/tree.html', success=result)

        elif list_warning in session:
            result = session["warning"]
            session.pop("warning")
            return render_template('admin/crush/tree.html', warning=result)

        else:
            return render_template('admin/crush/tree.html')


@crush_controller.route('/crush/save', methods=['GET', 'POST'])
@requires_auth
@authorization("BucketTree")
def save_bucket_tree():
    if request.method == 'POST':
        try:
            bucket_tree = request.form.get("bucket")
            manage_crush = ManageCrush()
            manage_crush.save_buckets_tree(bucket_tree)
            session['success'] = "ui_admin_save_buckets_success"
            return redirect(url_for('crush_controller.get_bucket_list'))

        except CrushException as e:
            if e.id == CrushException.COMPILE or e.id == CrushException.BUCKET_SAVE:
                session['err'] = "ui_admin_save_buckets_fail"
                logger.error(e)
                return redirect(url_for('crush_controller.get_bucket_list'))
            elif e.id == CrushException.BUCKET_NOT_DEFINED:
                session['err'] = "ui_admin_save_buckets_fail"
                logger.error(e)
                return redirect(url_for('crush_controller.get_bucket_list'))
            elif e.id == CrushException.DUPLICATE_BUCKET_NAME:
                session['err'] = "ui_admin_bucket_duplicate_name"
                logger.error(e)
                return redirect(url_for('crush_controller.get_bucket_list'))
            else:
                session['err'] = "ui_admin_save_buckets_fail"
                logger.error(e)
                return redirect(url_for('crush_controller.get_bucket_list'))

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
                logger.error(e)
                return redirect(url_for('crush_controller.get_bucket_list'))

            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
                logger.error(e)
                return redirect(url_for('crush_controller.get_bucket_list'))

            session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return redirect(url_for('crush_controller.get_bucket_list'))

        except Exception as e:
            session['err'] = "ui_admin_save_buckets_fail"
            logger.error(e)
            return redirect(url_for('crush_controller.get_bucket_list'))


@crush_controller.route('/crush/tree/read/<buckets_types>', methods=['GET'])
@requires_auth
def read_crush_tree(buckets_types):
    if request.method == 'GET':
        try:
            bucket_list_types = []
            types = buckets_types.split(",")
            print(type(types))
            manage_crush = ManageCrush()
            bucket_tree = manage_crush.get_buckets_tree(types)
            print(bucket_tree)
            return bucket_tree
        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
            else:
                session['err'] = "ui_admin_ceph_general_exception"
            return redirect(url_for('crush_controller.get_bucket_list'), 307)
        except Exception as e:
            session['err'] = "ui_admin_error_read_crush_map"
            logger.error(e)
            return redirect(url_for('crush_controller.get_bucket_list'))



@crush_controller.route('/crush/tree/read_buckets_types', methods=['GET'])
@requires_auth
def get_buckets_types():
    if request.method == 'GET':
        try:
            manage_crush = ManageCrush()
            buckets_types = manage_crush.get_buckets_types()
            return buckets_types

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
            else:
                session['err'] = "ui_admin_ceph_general_exception"
            return redirect(url_for('crush_controller.get_bucket_list'), 307)
        except Exception as e:
            session['err'] = "ui_admin_error_read_crush_map"
            logger.error(e)
            return redirect(url_for('crush_controller.get_bucket_list'))


@crush_controller.route('/crush/rules', methods=['GET'])
@requires_auth
@authorization("RulesList")
def get_rules_list():
    """
    DOCSTRING : this function get all the rules then render to the page : 'admin/crush/rules_list.html'.
    Args : None
    Returns : render to the template page : 'admin/crush/rules_list.html'
    """
    if request.method == 'GET':
        try:
            manage_crush = ManageCrush()
            rule_list = manage_crush.get_rules()

            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('admin/crush/rules_list.html', rule_list=rule_list, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('admin/crush/rules_list.html', rule_list=rule_list, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('admin/crush/rules_list.html', rule_list=rule_list, warning=result)

            else:
                return render_template('admin/crush/rules_list.html', rule_list=rule_list)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return render_template('admin/crush/rules_list.html')

        except Exception as e:
            session['err'] = "ui_admin_view_rule_error"
            result = session['err']
            logger.error(e)
            return render_template('admin/crush/rules_list.html', err=result)


@crush_controller.route('/crush/delete_rule/remove/<rule_name>', methods=['POST'])
@requires_auth
@authorization("RulesList")
def remove_rule(rule_name):
    """
    DOCSTRING : this function is called to delete a certain rule , then redirect to the page :
    'admin/crush/rules_list.html'.
    Args : rule_name (string)
    Returns : redirect to the page : 'admin/crush/rules_list.html'
    """
    if request.method == 'POST':
        try:
            used_flag = rule_in_use(rule_name)

            if used_flag:
                session["err"] = "ui_admin_cannot_delete_rule_in_use"
                return redirect(url_for('crush_controller.get_rules_list'))

            manage_crush = ManageCrush()

            manage_crush.delete_rule(rule_name)
            session["success"] = "ui_admin_delete_rule_success"
            return redirect(url_for('crush_controller.get_rules_list'))

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
                return redirect(url_for('crush_controller.get_rules_list'))

            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
                return redirect(url_for('crush_controller.get_rules_list'))

            session['err'] = "ui_admin_ceph_general_exception"
            return redirect(url_for('crush_controller.get_rules_list'))

        except Exception as e:
            session['err'] = "ui_admin_delete_rule_error"
            logger.error(e)
            return redirect(url_for('crush_controller.get_rules_list'))


@requires_auth
def rule_in_use(rule_name):
    """
    DOCSTRING : this function checks if a specific rule is used by a pool or not ...
    Args : rule_name (string)
    Returns : The return value is True if it used by a pool , False otherwise.
    """
    status = False
    manage_pools = ManagePools()
    pools_info = manage_pools.get_pools_info()  # List of objects of pool entity
    for pool_object in pools_info:
        if pool_object.rule_name == rule_name:
            status = True
    return status


@crush_controller.route('/rule/add', methods=['GET', 'POST'])
@requires_auth
@authorization("RulesList")
def rule_templates_list():
    """
    DOCSTRING : this function is called when opening the Add Rule form page.
    Args : None
    Returns : render to the template page : 'admin/crush/add_rule.html'
    """
    if request.method == 'GET' or request.method == 'POST':
        try:
            rule_info = request.args.get('rule_info')
            rules_templates = {}
            manage_crush = ManageCrush()
            rules_templates = manage_crush.get_templates()
            # rules_templates = {'name': 'body'}

            if list_err in session:
                result = session[list_err]
                session.pop(list_err)
                return render_template('admin/crush/add_rule.html', ruleTempList=rules_templates, err=result,
                                       rule_info=rule_info)

            elif list_warning in session:
                result = session[list_warning]
                session.pop(list_warning)
                return render_template('admin/crush/add_rule.html', ruleTempList=rules_templates, warning=result,
                                       rule_info=rule_info)

            elif list_success in session:
                result = session[list_success]
                session.pop(list_success)
                return render_template('admin/crush/add_rule.html', ruleTempList=rules_templates, success=result,
                                       rule_info=rule_info)

            else:
                return render_template('admin/crush/add_rule.html', ruleTempList=rules_templates, rule_info=rule_info)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                result = session['err'] = "ui_admin_ceph_time_out"
                return render_template('admin/crush/add_rule.html', ruleTempList=rules_templates, err=result,
                                       rule_info=rule_info)

            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
                return render_template('admin/crush/add_rule.html', ruleTempList=rules_templates, err=result,
                                       rule_info=rule_info)

            session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return render_template('admin/crush/add_rule.html', ruleTempList=rules_templates, err=result,
                                   rule_info=rule_info)


@crush_controller.route('/rule/save', methods=['POST'])
@requires_auth
@authorization("RulesList")
def save_rule():
    """
    DOCSTRING : this function is called at saving a new rule , if saving operation is succeeded it renders to the
    template page : 'admin/crush/rules_list.html' with a success message , and if not it redirects
    to : 'admin/crush/add_rule.html' with an error message ...
    Args : None
    Returns : in success , it renders to : 'admin/crush/rules_list.html' with a success message
    in failure , it redirects to : 'admin/crush/add_rule.html'
    """
    if request.method == 'POST':
        try:
            rule_name = (request.form['rule_name'])
            rule_info = (request.form['rule_body'])

            manage_crush = ManageCrush()
            rule_list = manage_crush.get_rules()

            if not unique_rule_name(rule_list, rule_name):
                session['err'] = "ui_admin_add_rule_err_duplicate"
                return redirect(
                    url_for('crush_controller.rule_templates_list'))

            manage_crush.add_rule(rule_name, rule_info)

            session['success'] = "ui_admin_add_rule_success"
            return redirect(url_for('crush_controller.get_rules_list'))

        except CrushException as e:

            if e.id == CrushException.RULE_SAVE:
                session['err'] = "ui_admin_crush_add_rule_error"
                return redirect(
                    url_for('crush_controller.rule_templates_list'))

            elif e.id == CrushException.DUPLICATE_RULE_NAME:
                session['err'] = "ui_admin_crush_duplicate_add_rule_error"
                return redirect(
                    url_for('crush_controller.rule_templates_list'))

            elif e.id == CrushException.DUPLICATE_RULE_ID:
                session['err'] = "ui_admin_crush_duplicate_id_add_rule_error"
                return redirect(
                    url_for('crush_controller.rule_templates_list'))

            elif e.id == CrushException.DEVICE_TYPE_NOT_EXISTS:
                session['err'] = "ui_admin_crush_osd_type_add_rule_error"
                return redirect(
                    url_for('crush_controller.rule_templates_list'))

            session['err'] = "ui_admin_crush_general_error"
            logger.error(e)
            return redirect(url_for('crush_controller.rule_templates_list'))

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
                return redirect(
                    url_for('crush_controller.rule_templates_list'))

            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
                return redirect(
                    url_for('crush_controller.rule_templates_list'))

            session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return redirect(url_for('crush_controller.rule_templates_list'))

        except Exception as e:
            session['err'] = "ui_admin_add_rule_err"
            logger.error(e)
            return redirect(url_for('crush_controller.rule_templates_list'))


@crush_controller.route('/rule/edit/<rule_name>', methods=['GET', 'POST'])
@requires_auth
@authorization("RulesList")
def get_rule_by_name(rule_name):
    """
    DOCSTRING : this function is called when opening the Edit Rule form page.
    Args : rule_name (string)
    Returns : redirect to the page : 'admin/crush/edit_rule.html'
    """
    if request.method == 'GET' or request.method == 'POST':
        try:
            manage_crush = ManageCrush()
            rule_list = manage_crush.get_rules()

            selected_rule_info = rule_list[rule_name]
            # selected_rule = {rule_name: selected_rule_info}

            rule_id = int(request.args.get('rule_id'))
            if rule_id == 0:
                result = "ui_admin_edit_default_rule"
                return render_template('admin/crush/edit_rule.html', rule_name=rule_name,
                                       selected_rule_info=selected_rule_info, info=result, rule_id=rule_id)
            if list_err in session:
                result = session[list_err]
                session.pop(list_err)
                return render_template('admin/crush/edit_rule.html', rule_name=rule_name,
                                       selected_rule_info=selected_rule_info, err=result, rule_id=rule_id)

            elif list_warning in session:
                result = session[list_warning]
                session.pop(list_warning)
                return render_template('admin/crush/edit_rule.html', rule_name=rule_name,
                                       selected_rule_info=selected_rule_info, warning=result, rule_id=rule_id)

            elif list_success in session:
                result = session[list_success]
                session.pop(list_success)
                return render_template('admin/crush/edit_rule.html', rule_name=rule_name,
                                       selected_rule_info=selected_rule_info, success=result, rule_id=rule_id)

            else:
                return render_template('admin/crush/edit_rule.html', rule_name=rule_name,
                                       selected_rule_info=selected_rule_info, rule_id=rule_id)
        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                result = session['err'] = "ui_admin_ceph_time_out"
                return render_template('admin/crush/edit_rule.html', rule_name=rule_name,
                                       selected_rule_info=selected_rule_info, err=result, rule_id=rule_id)

            elif e.id == CephException.GENERAL_EXCEPTION:
                result = session['err'] = "ui_admin_ceph_general_exception"
                logger.error(e)
                return render_template('admin/crush/edit_rule.html', rule_name=rule_name,
                                       selected_rule_info=selected_rule_info, err=result, rule_id=rule_id)

            result = session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return render_template('admin/crush/edit_rule.html', rule_name=rule_name,
                                   selected_rule_info=selected_rule_info, err=result, rule_id=rule_id)


@crush_controller.route('/rule/save_edit', methods=['POST'])
@requires_auth
@authorization("RulesList")
def edit_rule():
    """
    DOCSTRING : this function is called at editing a specific rule , if editing operation is succeeded it renders to the
    template page : 'admin/crush/rules_list.html' with a success message , and if not it redirects
    to : 'admin/crush/edit_rule.html' with an error message ...
    Args : None
    Returns : in success , it renders to : 'admin/crush/rules_list.html' with a success message
    in failure , it redirects to : 'admin/crush/edit_rule.html'
    """
    if request.method == 'POST':
        try:
            rule_name = request.form['rule_name']
            rule_id = request.form['rule_id']
            rule_info = request.form['rule_body']

            manage_crush = ManageCrush()
            # rule_list = manage_crush.get_rules()
            manage_crush.update_rule(rule_name, rule_info)

            session['success'] = "ui_admin_edit_rule_success"
            return redirect(url_for('crush_controller.get_rules_list'))

        except CrushException as e:
            if e.id == CrushException.RULE_SAVE:
                session['err'] = "ui_admin_crush_edit_rule_error"
                return redirect(url_for('crush_controller.get_rule_by_name', rule_name=rule_name, rule_id=rule_id))

            elif e.id == CrushException.DUPLICATE_RULE_ID:
                session['err'] = "ui_admin_crush_edit_duplicate_id_rule_error"
                return redirect(url_for('crush_controller.get_rule_by_name', rule_name=rule_name, rule_id=rule_id))


            elif e.id == CrushException.DEVICE_TYPE_NOT_EXISTS:
                session['err'] = "ui_admin_crush_osd_type_edit_rule_error"
                return redirect(
                    url_for('crush_controller.rule_templates_list', rule_name=rule_name, rule_info=rule_info))

            session['err'] = "ui_admin_crush_general_error"
            logger.error(e)
            return redirect(url_for('crush_controller.get_rule_by_name', rule_name=rule_name, rule_id=rule_id))

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
                return redirect(url_for('crush_controller.get_rule_by_name', rule_name=rule_name, rule_id=rule_id))

            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
                return redirect(url_for('crush_controller.get_rule_by_name', rule_name=rule_name, rule_id=rule_id))

            session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return redirect(url_for('crush_controller.get_rule_by_name', rule_name=rule_name, rule_id=rule_id))

        except Exception as e:
            session['err'] = "ui_admin_edit_rule_err"
            logger.error(e)
            return redirect(url_for('crush_controller.get_rule_by_name', rule_name=rule_name, rule_id=rule_id), 307)


def unique_rule_name(rules_list, rule_name):
    """
    DOCSTRING : this function checks on the uniqueness of the rule name ...
    Args : rule_name (string) , rules_list
    Returns : The return value is True if the rule name is taken , False otherwise.
    """
    status = True
    for key in rules_list:
        if key == rule_name:
            status = False
    return status

# ======================================================================================================================
# End of Manage Rule
# ======================================================================================================================

# get selected rule information as json data to use it in ajax call


@crush_controller.route('/rule/<rule_name>')
@requires_auth
@authorization("RulesList")
def get_selected_rule_info(rule_name):
    try:
        manage_crush = ManageCrush()
        rule_list = manage_crush.get_rules()

        selected_rule_info = rule_list[rule_name]
        json_data = json.dumps(selected_rule_info)
        return json_data

    except CephException as e:
        if e.id == CephException.CONNECTION_TIMEOUT:
            session['err'] = "ui_admin_ceph_time_out"
        elif e.id == CephException.GENERAL_EXCEPTION:
            session['err'] = "ui_admin_ceph_general_exception"
        logger.error(e)
        return render_template('admin/crush/rules_list.html')

    except Exception as e:
        session['err'] = "ui_admin_view_rule_error"
        result = session['err']
        logger.error(e)
        return render_template('admin/crush/rules_list.html', err=result)
