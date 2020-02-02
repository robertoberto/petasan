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

from flask import Blueprint, render_template, request, redirect, url_for, session , json
from PetaSAN.core.common.CustomException import CephException , ECProfileException
from PetaSAN.core.entity.models.ec_profile import ECProfile
from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.core.common.log import logger
from PetaSAN.backend.manage_ec_profiles import ManageEcProfiles

ec_profile_controller = Blueprint('ec_profile_controller', __name__)

list_err = "err"
list_warning = "warning"
list_success = "success"

@ec_profile_controller.route('/configuration/ec_profiles/', methods=['GET', 'POST'])
@requires_auth
@authorization("ProfilesList")
def get_ec_profiles():
    if request.method == 'GET' or request.method == 'POST':
        try:
            manageProfiles = ManageEcProfiles()
            profiles_list = manageProfiles.get_ec_profiles()
            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('admin/ec_profile/profiles_list.html' , err = result , profiles_list = profiles_list)
            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('admin/ec_profile/profiles_list.html' , success = result , profiles_list = profiles_list)
            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('admin/ec_profile/profiles_list.html' , warning = result , profiles_list = profiles_list)
            return render_template('admin/ec_profile/profiles_list.html' , profiles_list = profiles_list)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                result = session['err'] = "ui_admin_ceph_time_out"
            elif e.id == CephException.GENERAL_EXCEPTION:
                result = session['err'] = "ui_admin_ceph_general_exception"
            else:
                result = session['err'] = "ui_admin_ceph_general_exception"
                logger.error(e)
            return render_template('admin/ec_profile/profiles_list.html' , err = result)




@ec_profile_controller.route('/ec_profile/add', methods=['GET', 'POST'])
@requires_auth
@authorization("ProfilesList")
def add_ec_profile():
    if request.method == 'GET' or request.method == 'POST':
        try:
            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('admin/ec_profile/add_ec_profile.html', err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('admin/ec_profile/add_ec_profile.html', success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('admin/ec_profile/add_ec_profile.html', warning=result)

            return render_template('admin/ec_profile/add_ec_profile.html')

        except Exception as e:
            session['err'] = "ui_admin_error_loading_page"
            logger.error(e)
            return render_template('admin/ec_profile/add_ec_profile.html')




@ec_profile_controller.route('/ec_profile/remove/<profile_name>', methods=['GET', 'POST'])
@requires_auth
@authorization("ProfilesList")
def remove_profile(profile_name):
    if request.method == 'GET' or request.method == 'POST':
        try:
            manageProfiles = ManageEcProfiles()
            manageProfiles.delete_ec_profile(profile_name)
            session['success'] = "ui_admin_delete_ecProfile_success"
            return redirect(url_for('ec_profile_controller.get_ec_profiles'))

        except ECProfileException as e:
            if e.id == ECProfileException.ECPROFILE_IN_USE:
                session['err'] = "ui_admin_delete_ecProfile_fail_in_use"
                return redirect(url_for('ec_profile_controller.get_ec_profiles'))

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
                return redirect(url_for('ec_profile_controller.get_ec_profiles'))

            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
                return redirect(url_for('ec_profile_controller.get_ec_profiles'))

            session['err'] = "ui_admin_ceph_general_exception"
            return redirect(url_for('ec_profile_controller.get_ec_profiles'))

        except Exception as e:
            session['err'] = "ui_admin_delete_ecProfile_error"
            logger.error(e)
            return redirect(url_for('ec_profile_controller.get_ec_profiles'))




@ec_profile_controller.route('/ec_profile/get/<profile_name>' , methods=['GET'])
@requires_auth
@authorization("ProfilesList")
def get_profile_info(profile_name):
    if request.method == "GET":
        try:
            manageProfiles = ManageEcProfiles()
            profiles_list = manageProfiles.get_ec_profiles()
            profile_info = profiles_list[profile_name]
            print (profile_info.name)
            return json.dumps(profile_info.__dict__)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                result = session['err'] = "ui_admin_ceph_time_out"
            elif e.id == CephException.GENERAL_EXCEPTION:
                result = session['err'] = "ui_admin_ceph_general_exception"
            else:
                result = session['err'] = "ui_admin_ceph_general_exception"
                logger.error(e)
            return render_template('admin/ec_profile/profiles_list.html' , err = result)




@ec_profile_controller.route('/ec_profile/save' , methods=['POST'])
@requires_auth
@authorization("ProfilesList")
def save_ec_profile():
    if request.method == 'POST':
        try:
            manage_profile = ManageEcProfiles()
            profile_info = ECProfile()
            profile_info.name = request.form['profile_name']
            profile_info.k = int(request.form['k'])
            profile_info.m = int(request.form['m'])
            plugin = request.form['plugin']
            technique = request.form['technique']
            stripe_unit = request.form['stripe_unit']
            packet_size = request.form['packet_size']
            locality = request.form['locality']
            durability_estimator = request.form['durability_estimator']
            advanced = request.form['advanced']
            if advanced == "checked":
                if plugin is not None and plugin != "":
                    profile_info.plugin = plugin
                if technique is not None and technique != "":
                    profile_info.technique = technique
                if stripe_unit is not None and stripe_unit != "":
                    profile_info.strip_unit = stripe_unit
                if packet_size is not None and packet_size != "":
                    profile_info.packet_size = packet_size
                if locality is not None and locality != "":
                    profile_info.locality = locality
                if durability_estimator is not None and durability_estimator != "":
                    profile_info.durability_estimator = durability_estimator
            manage_profile.add_ec_profile(profile_info)
            session['success'] = "ui_admin_profile_saved_success"
            return redirect(url_for("ec_profile_controller.get_ec_profiles"))

        except ECProfileException as e:
            if e.id == ECProfileException.DUPLICATE_ECPROFILE_NAME:
                session['err'] = "ui_admin_add_ecProfile_fail_name_is_use"
                return redirect(url_for('ec_profile_controller.add_ec_profile'))

            elif e.id == ECProfileException.WRONG_ECPROFILE_LOCALITY_VALUE:
                session['err'] = "ui_admin_add_ecProfile_fail_wrong_k_value"
                return redirect(url_for('ec_profile_controller.add_ec_profile'))

            elif e.id == ECProfileException.INVALID_STRIPE_UNIT_ARGUMENT:
                session['err'] = "ui_admin_add_ecProfile_fail_stripe_unit"
                return redirect(url_for('ec_profile_controller.add_ec_profile'))

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
                return redirect(url_for('ec_profile_controller.add_ec_profile'))

            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
                return redirect(url_for('ec_profile_controller.add_ec_profile'))

            session['err'] = "ui_admin_ceph_general_exception"
            return redirect(url_for('ec_profile_controller.add_ec_profile'))

        except Exception as e:
            session['err'] = "ui_admin_add_ecProfile_error"
            logger.error(e)
            return redirect(url_for('ec_profile_controller.add_ec_profile'))








































