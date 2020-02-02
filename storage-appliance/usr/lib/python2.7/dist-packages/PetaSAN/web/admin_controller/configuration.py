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

from flask import Blueprint, render_template, request, redirect, url_for, session

from PetaSAN.core.entity.status import EmailStatus
from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.core.entity.models.configuration import manage_network_form
from PetaSAN.core.entity.models.cluster_config_form import ClusterConfigForm
from PetaSAN.core.common.log import logger
from PetaSAN.backend.manage_config import ManageConfig
from PetaSAN.core.entity.iscsi_subnet import ISCSISubnet
from PetaSAN.core.ceph.api import CephAPI

configuration_controller = Blueprint('configuration_controller', __name__)

list_err = "err"
list_warning = "warning"
list_success = "success"


@configuration_controller.route('/configuration/IscsiSettings', methods=['POST', 'GET'])
@requires_auth
@authorization("NetworkConfiguration")
def manage_network():
    if request.method == 'GET' or request.method == 'POST':
        result = ""

        if list_err in session:
            result = session[list_err]
            session.pop(list_err)
            return render_template('admin/configuration/network.html', err=result, form=request.form)
        elif list_warning in session:
            result = session[list_warning]
            session.pop(list_warning)
            return render_template('admin/configuration/network.html', warning=result, form=request.form)
        elif list_success in session:
            result = session[list_success]
            session.pop(list_success)
            return render_template('admin/configuration/network.html', success=result, form=request.form)
        else:
            result = "ui_admin_vlan_paths"
            form1 = manage_network_form()
            manage_configuration = ManageConfig()
            subnet1_Info = manage_configuration.get_iscsi1_subnet()
            subnet2_Info = manage_configuration.get_iscsi2_subnet()
            form1.Subnet1 = subnet1_Info.subnet_mask
            form1.Subnet1_Ip_From = subnet1_Info.auto_ip_from
            form1.Subnet1_Ip_To = subnet1_Info.auto_ip_to
            form1.Subnet1_Vlan_Id = subnet1_Info.vlan_id
            form1.Subnet2 = subnet2_Info.subnet_mask
            form1.Subnet2_Ip_From = subnet2_Info.auto_ip_from
            form1.Subnet2_Ip_To = subnet2_Info.auto_ip_to
            form1.Subnet2_Vlan_Id = subnet2_Info.vlan_id
            manage_configuration = ManageConfig()
            iqn = manage_configuration.get_iqn_base()
            form1.Iqn = iqn
            return render_template('admin/configuration/network.html', form=form1,info = result)


@configuration_controller.route('/configuration/GeneralSettings', methods=['GET'])
@requires_auth
@authorization("InternetTimeServer")
def manage_cluster_setting():
    if request.method == 'GET':
        result = ""
        if list_err in session:
            result = session[list_err]
            session.pop(list_err)
            return render_template('admin/configuration/cluster_settings.html', err=result, form=request.form)
        elif list_warning in session:
            result = session[list_warning]
            session.pop(list_warning)
            return render_template('admin/configuration/cluster_settings.html', warning=result, form=request.form)
        elif list_success in session:
            result = session[list_success]
            session.pop(list_success)
            cluster_config_model = ClusterConfigForm()
            manage_configuration = ManageConfig()
            new_cephAPI = CephAPI()
            # replica_no = new_cephAPI.get_replicas()
            # cluster_config_model.replica_no = replica_no
            # compression_algorithm = manage_configuration.get_compression_algorithm()
            # cluster_config_model.compression_algorithm = compression_algorithm
            # compression_mode = manage_configuration.get_compression_mode()
            # cluster_config_model.compression_mode = compression_mode
            internet_time_server = manage_configuration.get_ntp_server()
            app_config = ManageConfig().get_app_config()
            if app_config.email_notify_smtp_server != "":
                cluster_config_model.smtp_server = app_config.email_notify_smtp_server
                cluster_config_model.smtp_port = app_config.email_notify_smtp_port
                cluster_config_model.smtp_email = app_config.email_notify_smtp_email
                cluster_config_model.smtp_passwod = app_config.email_notify_smtp_password
                cluster_config_model.authentication_value = app_config.email_notify_smtp_security
            if internet_time_server == None:
                cluster_config_model.internet_time_server = ""
            else:
                cluster_config_model.internet_time_server = internet_time_server
            return render_template('admin/configuration/cluster_settings.html', success=result,
                                   form=cluster_config_model)
        else:
            cluster_config_model = ClusterConfigForm
            manage_configuration = ManageConfig()
            new_cephAPI = CephAPI()
            # replica_no = new_cephAPI.get_replicas()
            # cluster_config_model.replica_no = replica_no
            # compression_algorithm = manage_configuration.get_compression_algorithm()
            # cluster_config_model.compression_algorithm = compression_algorithm
            # compression_mode = manage_configuration.get_compression_mode()
            # cluster_config_model.compression_mode = compression_mode
            internet_time_server = manage_configuration.get_ntp_server()
            app_config = ManageConfig().get_app_config()
            if app_config.email_notify_smtp_server != "":
                cluster_config_model.smtp_server = app_config.email_notify_smtp_server
                cluster_config_model.smtp_port = app_config.email_notify_smtp_port
                cluster_config_model.smtp_email = app_config.email_notify_smtp_email
                cluster_config_model.smtp_passwod = app_config.email_notify_smtp_password
                cluster_config_model.authentication_value = app_config.email_notify_smtp_security
            if internet_time_server == None:
                cluster_config_model.internet_time_server = ""
            else:
                cluster_config_model.internet_time_server = internet_time_server
            return render_template('/admin/configuration/cluster_settings.html', form=cluster_config_model)


@configuration_controller.route('/configuration/GeneralSettings/save', methods=['POST'])
@requires_auth
@authorization("InternetTimeServer")
def save_cluster_setting():
    if request.method == 'POST':
        try:
            internet_time_server_val = request.form['internet_time_server']
            manage_configuration = ManageConfig()
            res = manage_configuration.save_ntp_server(internet_time_server_val)
            if res == False or res == None:
                manage_configuration.save_ntp_server("")
                logger.info("No NTP server Set")
        except Exception as e:
            session['err'] = "ui_admin_exep_err_save_NTP"
            logger.error(" error saving ntp server")
            return redirect(url_for('configuration_controller.manage_cluster_setting'), 307)
        # try:
        #     compression_mode = request.form['compression']
        #     compression_mode = int(compression_mode)
        #     if compression_mode == 2:
        #         algorithm = request.form['compression_algorithm_value']
        #         manage_configuration.set_compression_mode(compression_mode)
        #         manage_configuration.set_compression_algorithm(int(algorithm))
        #     else:
        #         manage_configuration.set_compression_mode(compression_mode)
        # except Exception as e:
        #     logger.error("Error Saving Compression")
        #     session['err'] = "ui_admin_error_set_data_compression"
        #     return redirect(url_for('configuration_controller.manage_cluster_setting'), 307)

        try:

            if 'smtp_server' in request.form:
                if request.form['smtp_server'] != "":
                    server = request.form['smtp_server']
                    port = int(request.form['port_no'])
                    email = str(request.form['email'])
                    passwod = request.form['userPassword']
                    authentication_value = int(request.form['authentication_value'])
                    manage_configuration.set_smtp_config(server, port, email, passwod, authentication_value)
                    session['success'] = "ui_admin_save_general_settings_success"
                    return redirect(url_for('configuration_controller.manage_cluster_setting'))
                else:
                    server = ""
                    port = ""
                    email = ""
                    passwod = ""
                    authentication_value = "1"
                    manage_configuration.set_smtp_config(server, port, email, passwod, authentication_value)
                    session['success'] = "ui_admin_save_general_settings_success"
                    return redirect(url_for('configuration_controller.manage_cluster_setting'))
        except Exception as e:
            logger.error("error set smtp settings")
            session['err'] = "ui_admin_error_set_smtp_settings"
            return redirect(url_for('configuration_controller.manage_cluster_setting'), 307)
            # try:
            #     mange_config = ManageConfig()
            #     replica_no = int(request.form['replica_no'])
            #     old_replica = int(mange_config.get_replicas())
            #     if replica_no != old_replica:
            #         res = mange_config.set_replicas(replica_no)
            #         if res == REPLICASSAVESTATUS.done:
            #             session['success'] = "ui_admin_set_replicas_value_success"
            #             return redirect(url_for('configuration_controller.manage_cluster_setting'))
            #         elif res == REPLICASSAVESTATUS.min_size_wrn:
            #             session['Warning'] = "ui_admin_warn_set_min_replicas"
            #             return redirect(url_for('configuration_controller.manage_cluster_setting'), 307)
            #         elif res == REPLICASSAVESTATUS.error:
            #             session['err'] = "ui_admin_error_set_replicas_value"
            #             return redirect(url_for('configuration_controller.manage_cluster_setting'), 307)
            #     else:
            #         session['success'] = "ui_admin_set_replicas_value_success"
            #         return redirect(url_for('configuration_controller.manage_cluster_setting'))
            # except Exception as e:
            #     session['err'] = "ui_admin_error_set_replicas_value"
            #     logger.error(e)
            #     return redirect(url_for('configuration_controller.manage_cluster_setting'), 307)


@configuration_controller.route('/configuration/IscsiSettings/save', methods=['POST', 'GET'])
@requires_auth
@authorization("NetworkConfiguration")
def save_network():
    if request.method == 'GET' or request.method == 'POST':
        try:

            iqn_val = request.form['Iqn']
            manage_configuration = ManageConfig()
            manage_configuration.set_iqn_base(iqn_val)
            subnet1 = request.form['Subnet1']
            subnet1_ip_from = request.form['Subnet1_Ip_From']
            subnet1_ip_to = request.form['Subnet1_Ip_To']
            subnet1_vlan_id = request.form['Subnet1_Vlan_Id']
            subnet2 = request.form['Subnet2']
            subnet2_ip_from = request.form['Subnet2_Ip_From']
            subnet2_ip_to = request.form['Subnet2_Ip_To']
            subnet2_vlan_id = request.form['Subnet2_Vlan_Id']

            form1 = manage_network_form()
            form1.Subnet1_Vlan_Id = subnet1_vlan_id
            form1.Subnet1_Vlan_Id = subnet2_vlan_id
            subnet1_info = ISCSISubnet()
            subnet1_info.subnet_mask = subnet1
            subnet1_info.auto_ip_from = subnet1_ip_from
            subnet1_info.auto_ip_to = subnet1_ip_to
            subnet1_info.vlan_id = subnet1_vlan_id

            subnet2_info = ISCSISubnet()
            subnet2_info.subnet_mask = subnet2
            subnet2_info.auto_ip_from = subnet2_ip_from
            subnet2_info.auto_ip_to = subnet2_ip_to
            subnet2_info.vlan_id = subnet2_vlan_id

            manage_configuration = ManageConfig()
            manage_configuration.set_iscsi1_subnet(subnet1_info)
            manage_configuration.set_iscsi2_subnet(subnet2_info)

            session['success'] = "ui_admin_network_suc"

            return redirect(url_for('configuration_controller.manage_network'), 307)

        except Exception as e:
            session['err'] = "ui_admin_network_err_exception"
            logger.error(e)
            return redirect(url_for('configuration_controller.manage_network'), 307)



        except Exception as e:
            session['err'] = " Error in Saving."
            logger.error(e)
            return redirect(url_for('configuration_controller.manage_disk'), 307)


@configuration_controller.route('/configuration/GeneralSettings/testEmail', methods=['POST'])
@requires_auth
@authorization("InternetTimeServer")
def test_email():
    if request.method == 'POST':
        status = EmailStatus()
        try:
            email = request.form['email']
            password = request.form['password']
            server = request.form['server']
            port = request.form['port']
            security = request.form['security']
            status = ManageConfig().test_email(email, server, port, password, security, session['user'])
            status.exception = str(status.exception)
            return status.write_json()

        except Exception as e:
            logger.error(e)
            status.success = False
            status.err_msg = e.message
            return status.write_json()
