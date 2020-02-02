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
from PetaSAN.backend.replication.manage_users import ManageUsers
from PetaSAN.core.cluster.network import Network
from PetaSAN.core.cluster.state_util import StateUtil
from PetaSAN.core.common.CustomException import SSHKeyException, JoinException, ReplaceException
from flask import Blueprint, render_template, request, redirect, url_for, session, Response, \
    stream_with_context
from PetaSAN.backend.cluster.deploy import Wizard
from PetaSAN.core.cluster.configuration import *
from PetaSAN.core.common.ip_utils import *
from PetaSAN.core.common.enums import Status, BuildStatus
from PetaSAN.core.common.messages import gettext
from PetaSAN.core.entity.models.EthernetInfo import EthernetInfo
from PetaSAN.core.entity.models.cluster import AddClusterInfoForm
from PetaSAN.core.entity.models.join_cluster import JoinClusterData
from PetaSAN.core.entity.models.build_status import executionStatus
from PetaSAN.core.common.enums import JoiningStatus, BondMode
from PetaSAN.backend.manage_node import ManageNode
from PetaSAN.core.ceph import ceph_disk_lib

wizard_controller = Blueprint('wizard_controller', __name__)

list_err = 'err'
list_warning = 'warning'
list_success = 'success'
err_number = 0

deployment_dict = {

    'landing_page': {
        'option': ''
    },

    'cluster_info_&_join': {
        'cluster_name': '',
        'cluster_ip': '',
        'success_msg': ''
    },

    'cluster_NIC_settings': {
        'jumbo_frames': False,
        'jf_interfaces': [],
        'NIC_bonding': False,
        'bonded_interfaces': [],
        'bonded_interfaces_list': [],
        'success_msg': ''
    },

    'cluster_network_sittings': {
        'iscsi_1_eth_name': '',
        'iscsi_2_eth_name': '',
        'backend_1_eth_name': '',
        'backend_2_eth_name': '',
        'backend_1_base_ip': '',
        'backend_2_base_ip': '',
        'backend_1_mask': '',
        'backend_2_mask': '',
        'vlan_tagging_backend1': False,
        'vlan_id_backend1': '',
        'vlan_tagging_backend2': False,
        'vlan_id_backend2': '',
        'success_msg': ''
    },

    'cluster_tuning': {
        'cluster_size': '',
        'replicas_no': '',
        'storage_engine': '',
        'tuning_template': '',
        'ceph_script': '',
        'lio_config': '',
        'post_script_config': '',
        'success_msg': ''
    },

    'node_network_setting': {
        'backend_1_ip': '',
        'backend_2_ip': '',
        'success_msg': ''
    },

    'node_services_form': {
        'is_iscsi': False,
        'is_storage': False,
        'is_backup': False,
        'osds': [],
        'journals': [],
        'success_msg': ''
    }
}

@wizard_controller.route('/', methods=['GET', 'POST'])
def main():
    ############################################################
    #                   Step 1 : Wizard Start                  #
    ############################################################
    deployment_json1 = json.dumps(deployment_dict)
    init_deploy_data = json.loads(deployment_json1)
    if "deployment_data" in session and "keep_data" not in session:
        session['deployment_data'] = init_deploy_data
    deploy_data = init_deploy_data
    if 'deployment_data' in session and 'keep_data' in session:
        deploy_data = session['deployment_data']
        session.pop('keep_data')
    if "submitted_page" not in session:
        new_wizard = Wizard()
        cluster_state = new_wizard.is_cluster_config_complated()
        management_urls = ""
        session['deployment_data'] = deploy_data
        node_status = new_wizard.get_node_status()
        if node_status == JoiningStatus.node_joined:
            status = "node joined"
            if cluster_state == True:
                status = "ui_deploy_landing_cluster_created"
                state = '20'
                management_urls = new_wizard.get_management_urls()
        elif node_status == JoiningStatus.one_node_exists:
            status = "ui_deploy_landing_two_node_required"
            state = None
        elif node_status == JoiningStatus.two_node_exist:
            status = "ui_deploy_landing_one_node_required"
            state = None
        elif node_status == JoiningStatus.not_joined:
            status = None
            state = '10'
        return render_template('deploy/landing_page.html', status=status, management_urls=management_urls,
                               deploy_data=deploy_data, state=state)

    else:
        page = session["submitted_page"]
        session.pop("submitted_page")

        ############################################################
        #               Step 3 : Cluster NIC Settings              #
        ############################################################
        if page == "cluster_interface_setting":
            if list_success in session:
                result = session[list_success]
                session.pop(list_success)
                new_wizard = Wizard()
                interfaces = new_wizard.get_node_eths()
                bond_modes = []
                for key, mode in BondMode.__dict__.items():
                    if not str(key).startswith("_"):
                        bond_modes.append(mode)
                bond_modes.sort()

                # Getting all interfaces info :
                # -----------------------------
                interfaces_info = new_wizard.get_interfaces_info()
                interfaces_json = json.dumps(interfaces_info)

                # Getting all interfaces names :
                # ------------------------------
                keys_ls = ""

                for key, value in interfaces_info.iteritems():
                    keys_ls = keys_ls + key + "-"

                keys_ls = keys_ls[:-1]

                return render_template('deploy/cluster_interface_setting.html', eths=interfaces,
                                       deploy_data=deploy_data, bond_modes=bond_modes,
                                       success=result, interfaces_json=interfaces_json, keys_ls=keys_ls)
            elif list_err in session:
                result = session[list_err]
                session.pop(list_err)
                return render_template('deploy/cluster_interface_setting.html', deploy_data=deploy_data, err=result)

        ############################################################
        #             Step 4 : Cluster Network Settings            #
        ############################################################
        elif page == "cluster_network_setting":
            eths = []
            new_network = Network()
            none_bonds_eths = new_network.get_none_bond_interfaces()
            management_eth = new_network.get_node_management_interface()
            management_base_ip = new_network.get_node_management_base_ip()
            management_netmask = new_network.get_node_management_netmask()
            management_vlan_id = new_network.get_node_management_vlan_id()
            new_configuration = configuration()
            bonds = new_configuration.get_cluster_bonds()
            for none_bond in none_bonds_eths:
                new_eth = EthernetInfo()
                new_eth.name = none_bond.name
                eths.append(new_eth)
            for bond in bonds:
                new_eth = EthernetInfo()
                new_eth.name = bond.name
                eths.append(new_eth)
            for eth in eths:
                if eth.name == management_eth:
                    eth.is_management = True
                    break
            if list_success in session:
                result = session[list_success]
                session.pop(list_success)
                return render_template('deploy/cluster_network_setting.html', eths=eths, success=result, flag="success",
                                       management_netmask=management_netmask, management_base_ip=management_base_ip,
                                       management_vlan_id=management_vlan_id, deploy_data=deploy_data)
            elif list_err in session:
                result = session[list_err]
                session.pop(list_err)
                return render_template('deploy/cluster_network_setting.html', err=result, flag="err",
                                       management_netmask=management_netmask, management_base_ip=management_base_ip,
                                       management_vlan_id=management_vlan_id, deploy_data=deploy_data)
            return render_template('deploy/cluster_network_setting.html', eths=eths, flag="success",
                                   management_netmask=management_netmask, management_base_ip=management_base_ip,
                                   management_vlan_id=management_vlan_id, deploy_data=deploy_data)

        ############################################################
        #              Step 3` : Replacement Settings              #
        ############################################################
        elif page == "node_summary_setting":
            if list_success in session:
                result = session[list_success]
                session.pop(list_success)
                new_wizard = Wizard()
                status = new_wizard.is_valid_network_setting()
                node_name = new_wizard.get_node_name()
                if status == True:
                    configuration_obj = configuration()
                    cluster_info = configuration_obj.get_cluster_info()
                    node_info = configuration_obj.get_node_info()
                    return render_template('deploy/node_summary_setting.html', node_name=node_name, success=result,
                                           cluster_info=cluster_info, node_info=node_info, deploy_data=deploy_data)
                elif status == False:
                    session['err'] = "ui_deploy_network_setting_invalid"
                    result = session[list_err]
                    session.pop(list_err)
                    return render_template('deploy/node_summary_setting.html', err=result, deploy_data=deploy_data)
            elif list_err in session:
                result = session[list_err]
                session.pop(list_err)
                return render_template('deploy/node_summary_setting.html', err=result, deploy_data=deploy_data)

        ############################################################
        #               Step 6 : Node Network Settings             #
        ############################################################
        elif page == "node_network_setting":
            new_wizard = Wizard()
            node_name = new_wizard.get_node_name()
            flag = ""
            come_from = session['come_from']
            if list_success in session:
                result = session[list_success]
                session.pop(list_success)
                status = new_wizard.is_valid_network_setting()
                if len(deploy_data['node_network_setting']['success_msg']) > 0:
                    status = True
                if status == True:
                    if (session["join"] == "join"):
                        flag = session['join']
                        # session.pop('join')
                    if result == "ui_deploy_save_cluster_tuning_setting_succ":
                        return render_template('deploy/node_network_setting.html', node_name=node_name,
                                               flag_1="success", flag_2=flag, come_from=come_from,
                                               deploy_data=deploy_data)

                    return render_template('deploy/node_network_setting.html', node_name=node_name, success=result,
                                           flag_1="success", flag_2=flag, come_from=come_from, deploy_data=deploy_data)
                elif status == False:
                    session['err'] = "ui_deploy_network_setting_invalid"
                    result = session[list_err]
                    session.pop(list_err)
                    return render_template('deploy/node_network_setting.html', err=result, node_name=node_name,
                                           flag_1="err", flag_2=flag, come_from=come_from, deploy_data=deploy_data)
            elif list_err in session:
                result = session[list_err]
                session.pop(list_err)
                if 'backend' in session:
                    flag = session['backend']
                    # session.pop('backend')
                return render_template('deploy/node_network_setting.html', err=result, node_name=node_name,
                                       flag_1="err", flag_2=flag, come_from=come_from, deploy_data=deploy_data)

        ############################################################
        #                   Step 7 : Node Services                 #
        ############################################################
        elif page == "node_role_setting":
            wizard = Wizard()
            manage_monitoring = wizard.is_cluster_config_complated()
            management_urls = []  # For setting Backfill Speed

            if manage_monitoring == True:
                manage_monitoring = False
                # For setting Backfill Speed
                management_urls = wizard.get_management_urls()

            elif manage_monitoring == False:
                manage_monitoring = True
            nodeName = wizard.get_node_name()
            if list_err in session:
                result = session[list_err]
                session.pop(list_err)
                disk_list = ceph_disk_lib.get_disk_list_deploy()
                return render_template('deploy/node_role_setting.html', err=result, node_name=nodeName,
                                       diskList=disk_list, management_urls=management_urls, deploy_data=deploy_data)
            if list_success in session:
                result = session[list_success]
                session.pop(list_success)
                disk_list = ceph_disk_lib.get_disk_list_deploy()
                return render_template('deploy/node_role_setting.html', success=result, node_name=nodeName,
                                       manage_monitoring=manage_monitoring, diskList=disk_list,
                                       management_urls=management_urls, deploy_data=deploy_data)

                ##########################################################
                #                   Step 2` : Join Cluster                 #
                ##########################################################
        elif page == "join_cluster":
            if list_err in session:
                if err_number == 10:
                    result = session[list_err]
                    session.pop(list_err)
                    form1 = JoinClusterData()
                    form1.ip = deploy_data['cluster_info_&_join']['cluster_ip']
                    return render_template('deploy/join_cluster.html', deploy_data=deploy_data, form=form1, err=result,
                                           err_num=err_number)
                else:
                    result = session[list_err]
                    session.pop(list_err)
                    form1 = JoinClusterData()
                    form1.ip = deploy_data['cluster_info_&_join']['cluster_ip']
                    return render_template('deploy/join_cluster.html', deploy_data=deploy_data, form=form1, err=result)
            else:
                form1 = JoinClusterData()
                form1.ip = deploy_data['cluster_info_&_join']['cluster_ip']
                result = " "
                return render_template('deploy/join_cluster.html', deploy_data=deploy_data, form=form1, err=result)

        ############################################################
        #            Step 2`` : Replace Management Node            #
        ############################################################
        elif page == "replace_node":
            if list_err in session:
                result = session[list_err]
                session.pop(list_err)
                form1 = JoinClusterData()
                form1.ip = deploy_data['cluster_info_&_join']['cluster_ip']
                return render_template('deploy/join_cluster.html', deploy_data=deploy_data, form=form1, err=result,
                                       flag="replace")
            else:
                form1 = JoinClusterData()
                result = " "
                form1.ip = deploy_data['cluster_info_&_join']['cluster_ip']
                return render_template('deploy/join_cluster.html', deploy_data=deploy_data, form=form1, err=result,
                                       flag="replace")

        ############################################################
        #                  Step 2 : Cluster Identity               #
        ############################################################
        elif page == "cluster_info":
            if list_err in session:
                result = session[list_err]
                session.pop(list_err)
                form1 = AddClusterInfoForm()
                return render_template('deploy/cluster_info.html', deploy_data=deploy_data, form=form1, err=result)

            else:
                form1 = AddClusterInfoForm()
                return render_template('deploy/cluster_info.html', deploy_data=deploy_data, form=form1)

        ############################################################
        #                   Step 5 : Cluster Tuning                #
        ############################################################
        elif page == "tuning_form":
            if list_success in session:
                result = session[list_success]
                session.pop(list_success)
                templates = configuration().get_template_names()
                return render_template('deploy/tuning_form.html', templates=templates, success=result,
                                       deploy_data=deploy_data)
            elif list_err in session:
                result = session[list_err]
                session.pop(list_err)
                return render_template('deploy/tuning_form.html', err=result, deploy_data=deploy_data)

        ############################################################
        #               Step 8 : Final Deployment Stage            #
        ############################################################
        elif page == "build_load":
            return render_template('deploy/build.html')


@wizard_controller.route('/cluster_network_setting/save', methods=['POST'])
def save_cluster_network_setting():
    if request.method == 'POST':
        try:
            new_cluster_info = ClusterInfo()
            new_cluster_info.iscsi_1_eth_name = request.form['iscsi_1_eth_name']
            new_cluster_info.iscsi_2_eth_name = request.form['iscsi_2_eth_name']
            new_cluster_info.backend_1_eth_name = request.form['backend_1_eth_name']
            new_cluster_info.backend_2_eth_name = request.form['backend_2_eth_name']
            new_cluster_info.backend_1_base_ip = request.form['backend_1_base_ip']
            new_cluster_info.backend_2_base_ip = request.form['backend_2_base_ip']
            new_cluster_info.backend_1_mask = request.form['backend_1_mask']
            new_cluster_info.backend_2_mask = request.form['backend_2_mask']
            if request.form.get('vlan_tagging_backend1'):
                new_cluster_info.backend_1_vlan_id = request.form['vlan_id_backend1']
                logger.info(int(request.form['vlan_id_backend1']))

            if request.form.get('vlan_tagging_backend2'):
                new_cluster_info.backend_2_vlan_id = request.form['vlan_id_backend2']
                logger.info(int(request.form['vlan_id_backend2']))

            # save network settings on the session to for previous button view
            deployment_data = session['deployment_data']
            deployment_data['cluster_network_sittings']['iscsi_1_eth_name'] = new_cluster_info.iscsi_1_eth_name
            deployment_data['cluster_network_sittings']['iscsi_2_eth_name'] = new_cluster_info.iscsi_2_eth_name
            deployment_data['cluster_network_sittings']['backend_1_eth_name'] = new_cluster_info.backend_1_eth_name
            deployment_data['cluster_network_sittings']['backend_2_eth_name'] = new_cluster_info.backend_2_eth_name
            deployment_data['cluster_network_sittings']['backend_1_base_ip'] = new_cluster_info.backend_1_base_ip
            deployment_data['cluster_network_sittings']['backend_2_base_ip'] = new_cluster_info.backend_2_base_ip
            deployment_data['cluster_network_sittings']['backend_1_mask'] = new_cluster_info.backend_1_mask
            deployment_data['cluster_network_sittings']['backend_2_mask'] = new_cluster_info.backend_2_mask
            deployment_data['cluster_network_sittings']['vlan_tagging_backend1'] = False
            deployment_data['cluster_network_sittings']['vlan_id_backend1'] = ""
            deployment_data['cluster_network_sittings']['vlan_tagging_backend2'] = False
            deployment_data['cluster_network_sittings']['vlan_id_backend2'] = ""
            if request.form.get('vlan_tagging_backend1'):
                deployment_data['cluster_network_sittings']['vlan_tagging_backend1'] = True
                deployment_data['cluster_network_sittings']['vlan_id_backend1'] = new_cluster_info.backend_1_vlan_id
            if request.form.get('vlan_tagging_backend2'):
                deployment_data['cluster_network_sittings']['vlan_tagging_backend2'] = True
                deployment_data['cluster_network_sittings']['vlan_id_backend2'] = new_cluster_info.backend_2_vlan_id
            session['deployment_data'] = deployment_data
            session['keep_data'] = True
            new_wizard = Wizard()
            status = new_wizard.set_cluster_network_info(new_cluster_info)

            if status == Status().done:
                session['success'] = "ui_deploy_save_cluster_network_setting_success"
                deployment_data['cluster_network_sittings']['success_msg'] = session['success']
                session['submitted_page'] = "tuning_form"
                return redirect(url_for('wizard_controller.main'))
            elif status == Status().error:
                session['err'] = "ui_deploy_save_cluster_network_setting_error"
                session['submitted_page'] = "cluster_network_setting"
                return redirect(url_for('wizard_controller.main'), err=session['err'])

        except Exception as e:
            session['err'] = "ui_deploy_save_cluster_network_setting_error"
            session['submitted_page'] = "cluster_network_setting"
            return redirect(url_for('wizard_controller.main'))


@wizard_controller.route('/back_cluster_network_setting/save', methods=['POST'])
def back_to_cluster_network_setting():
    if request.method == 'POST':
        try:
            deployment_data = session['deployment_data']
            session['success'] = deployment_data['cluster_NIC_settings']['success_msg']
            session['submitted_page'] = "cluster_network_setting"
            session['keep_data'] = True
            return redirect(url_for('wizard_controller.main'))
        except Exception as e:
            logger.error(e)
            return redirect(url_for('wizard_controller.main'), 307)


@wizard_controller.route('/node_network_setting/save', methods=['POST'])
def save_node_network_setting():
    if request.method == 'POST':
        try:
            new_node_info = NodeInfo()
            new_node_info.backend_1_ip = request.form['backend_ip_1']
            new_node_info.backend_2_ip = request.form['backend_ip_2']

            # save cluster tuning in deploy_data dict for previous button
            deployment_data = session['deployment_data']
            deployment_data['node_network_setting']['backend_1_ip'] = new_node_info.backend_1_ip
            deployment_data['node_network_setting']['backend_2_ip'] = new_node_info.backend_2_ip
            session['deployment_data'] = deployment_data
            session['keep_data'] = True

            new_configuration = configuration()
            cluster_info = new_configuration.get_cluster_info()

            if is_ip_in_subnet(new_node_info.backend_1_ip, cluster_info.backend_1_base_ip, cluster_info.backend_1_mask):
                if is_ip_in_subnet(new_node_info.backend_2_ip, cluster_info.backend_2_base_ip,
                                   cluster_info.backend_2_mask):
                    new_wizard = Wizard()
                    status = new_wizard.set_node_info(new_node_info)

                    if status == Status().done:
                        session['success'] = "ui_deploy_save_node_network_setting_success"
                        deployment_data['node_network_setting']['success_msg'] = session['success']
                        session['submitted_page'] = "node_role_setting"
                        return redirect(url_for('wizard_controller.main'))
                    elif status == Status().error:
                        session['err'] = "ui_deploy_save_node_network_setting_error"
                        session['submitted_page'] = "node_network_setting"
                        return redirect(url_for('wizard_controller.main'), 307)

                else:
                    session['err'] = "ui_deploy_save_node_network_setting_ip2_out_of_range"
                    session['submitted_page'] = "node_network_setting"
                    session['backend'] = "backend"
                    return redirect(url_for('wizard_controller.main'), 307)
            else:
                session['err'] = "ui_deploy_save_node_network_setting_ip1_out_of_range"
                session['submitted_page'] = "node_network_setting"
                session['backend'] = "backend"
                return redirect(url_for('wizard_controller.main'), 307)

        except Exception as e:
            session['err'] = "ui_deploy_save_node_network_setting_error"
            session['submitted_page'] = "node_network_setting"
            return redirect(url_for('wizard_controller.main'), 307)


@wizard_controller.route('/back_node_network_setting', methods=['POST'])
def back_to_node_network_setting():
    if request.method == 'POST':
        try:
            deployment_data = session['deployment_data']
            session['success'] = deployment_data['cluster_tuning']['success_msg']
            session['submitted_page'] = "node_network_setting"
            session['keep_data'] = True
            return redirect(url_for('wizard_controller.main'))
        except Exception as e:
            logger.error(e)
            return redirect(url_for('wizard_controller.main'), 307)


@wizard_controller.route('/wizerd/addCluster/saveCluster', methods=['POST'])
def save_cluster_info():
    if request.method == 'POST':
        try:
            wizerd = Wizard()
            name = request.form['name']
            cluster_password = request.form['clusterPassword']
            # save cluster info
            deployment_data = session['deployment_data']
            deployment_data['cluster_info_&_join']['cluster_name'] = name
            session['deployment_data'] = deployment_data
            session["keep_data"] = True
            status = wizerd.create_cluster_info(cluster_password, name)
            if status == Status.done:
                session['success'] = "ui_deploy_cluster_info_suc"
                deployment_data['cluster_info_&_join']['success_msg'] = session['success']
                # session['submitted_page'] = "cluster_network_setting"
                session['submitted_page'] = "cluster_interface_setting"
                return redirect(url_for('wizard_controller.main'))
            elif status == Status.error:
                session['err'] = "ui_deploy_cluster_info_err"
                session['submitted_page'] = "cluster_info"
                return redirect(url_for('wizard_controller.main'), 307)
        except Exception as e:
            session['err'] = "ui_deploy_cluster_info_err_exception"
            session['submitted_page'] = "cluster_info"
            logger.error(e)
            return redirect(url_for('wizard_controller.main'), 307)


@wizard_controller.route('/wizerd/toAddCluster', methods=['POST'])
def back_to_cluster_info():
    if request.method == 'POST':
        try:
            deployment_data = session['deployment_data']
            # session['success'] = deployment_data['']['success_msg']
            deployment_data = session['deployment_data']
            if deployment_data['landing_page']['option'] == 'create_cluster':
                session['submitted_page'] = "cluster_info"
            if deployment_data['landing_page']['option'] == 'join_cluster':
                session['submitted_page'] = "join_cluster"
            if deployment_data['landing_page']['option'] == 'replace_node':
                session['replace_node'] = "replace_node"
                session['submitted_page'] = "replace_node"
            session["keep_data"] = True
            return redirect(url_for('wizard_controller.main'))
        except Exception as e:
            logger.error(e)
            return redirect(url_for('wizard_controller.main'), 307)


@wizard_controller.route('/wizerd/joinCluster/saveJoinCluster', methods=['POST'])
def save_join_cluster():
    if request.method == 'POST':
        if "replace_node" not in session:
            try:
                wizard = Wizard()
                cluster_ip = request.form['cluterIP']
                cluster_password = request.form['clusterPassword']
                deployment_data = session['deployment_data']
                deployment_data['cluster_info_&_join']['cluster_ip'] = cluster_ip
                session['deployment_data'] = deployment_data
                cluster_name = wizard.join(cluster_ip, cluster_password)
                node_name = wizard.get_node_name()
                session['success'] = "ui_deploy_join_cluster_suc" + "%" + node_name + "%" + cluster_name
                deployment_data['cluster_info_&_join']['success_msg'] = session['success']
                session['submitted_page'] = "node_network_setting"
                session['join'] = "join"
                session['come_from'] = "join"
                session['keep_data'] = True
                return redirect(url_for('wizard_controller.main'))
            except Exception as e:
                if isinstance(e, SSHKeyException):
                    session['err'] = "ui_deploy_join_cluster_err_SSHKeyException"
                    session["submitted_page"] = "join_cluster"
                    logger.error(e)
                    return redirect(url_for('wizard_controller.main'), 307)
                elif isinstance(e, JoinException):
                    session['err'] = "ui_deploy_join_cluster_err_JoinException"
                    session["submitted_page"] = "join_cluster"
                    logger.error(e)
                    return redirect(url_for('wizard_controller.main'), 307)
                else:
                    session['err'] = "ui_deploy_join_cluster_err"
                    session['submitted_page'] = "join_cluster"
                    logger.error(e)
                    return redirect(url_for('wizard_controller.main'), 307)


        else:
            replace = session["replace_node"]

            if replace == "replace_node":
                try:
                    wizard = Wizard()
                    cluster_ip = request.form['cluterIP']
                    cluster_password = request.form['clusterPassword']
                    wizard.replace(cluster_ip, cluster_password)
                    session.pop("replace_node")
                    deployment_data = session['deployment_data']
                    deployment_data['cluster_info_&_join']['cluster_ip'] = cluster_ip
                    session['deployment_data'] = deployment_data
                    session['keep_data'] = True
                    # node_name = wizard.get_node_name()
                    session['success'] = "ui_deploy_replace_cluster_suc"
                    deployment_data['cluster_info_&_join']['success_msg'] = session['success']
                    session['submitted_page'] = "node_summary_setting"
                    return redirect(url_for('wizard_controller.main'))
                except Exception as e:

                    if isinstance(e, SSHKeyException):
                        session['err'] = "ui_deploy_replace_cluster_SSHKeyException"
                        # session["submitted_page"] = "join_cluster"
                        session['submitted_page'] = "replace_node"
                        # session["replace_node"] = "replace_node"
                        logger.error(e)
                        return redirect(url_for('wizard_controller.main'), 307)
                    elif isinstance(e, ReplaceException):
                        session['err'] = e.message
                        # session["submitted_page"] = "join_cluster"
                        session['submitted_page'] = "replace_node"
                        # session["replace_node"] = "replace_node"
                        logger.error(e)
                        return redirect(url_for('wizard_controller.main'), 307)
                    else:
                        session['err'] = "Error copying configuration."
                        # session['submitted_page'] = "join_cluster"
                        session['submitted_page'] = "replace_node"
                        # session["replace_node"] = "replace_node"
                        logger.error(e)
                        return redirect(url_for('wizard_controller.main'), 307)


    else:
        session['err'] = "ui_deploy_join_cluster_err_not_join"
        session['submitted_page'] = "join_cluster"
        return redirect(url_for('wizard_controller.main'), 307, err_number=10)


@wizard_controller.route('/landing_page', methods=['POST'])
def save_landing_page():
    deployment_data = session['deployment_data']
    if "replace_node" in session:
        session.pop("replace_node")
    if request.form['option'] == 'create':
        session['submitted_page'] = "cluster_info"
        deployment_data['landing_page']['option'] = "create_cluster"
    elif request.form['option'] == 'join':
        session['submitted_page'] = "join_cluster"
        deployment_data['landing_page']['option'] = "join_cluster"
    elif request.form['option'] == 'replace':
        session['submitted_page'] = "replace_node"
        session["replace_node"] = "replace_node"
        deployment_data['landing_page']['option'] = "replace_node"
    session['deployment_data'] = deployment_data
    session["keep_data"] = True
    return redirect(url_for('wizard_controller.main'))


@wizard_controller.route('/to_landing_page', methods=['POST'])
def back_to_landing_page():
    if "replace_node" in session:
        session.pop("replace_node")
    if "submitted_page" in session:
        session.pop('submitted_page')
    session["keep_data"] = True
    return redirect(url_for('wizard_controller.main'))


@wizard_controller.route('/node_role_setting/save', methods=['GET', 'POST'])
def save_node_role_setting():
    if request.method == "GET" or request.method == "POST":
        try:
            if request.form['option_iscsi'] == 'ISCSI':
                is_iscsi = True
        except Exception as ex:
            is_iscsi = False
            logger.error(ex)
        try:
            if request.form['option_storage'] == 'storage':
                is_storage = True
        except Exception as ex:
            is_storage = False
            logger.error(ex)
        try:
            if request.form['backup'] == 'backup_node':
                is_backup = True
        except Exception as ex:
            is_backup = False
            logger.error(ex)
    wizard = Wizard()
    osds = []
    journals = []
    cache_devices = []
    try:
        if is_storage:
            for key, val in request.form.iteritems():
                if str(val) == 'journal':
                    journals.append(str(key).replace('usage_', ''))
                elif str(val) == 'osd':
                    osds.append(str(key).replace('usage_', ''))
                elif str(val) == 'cache':
                    cache_device = dict()
                    cache_device[str(key).replace('usage_', '')] = "writecache"
                    cache_devices.append(cache_device)

            wizard.set_node_storage_disks(osds, journals,cache_devices)
    except Exception as ex:
        logger.error(ex)
        session['err'] = "Error saving node services settings"
        session['submitted_page'] = "node_role_setting"
        return redirect(url_for('wizard_controller.main'), 307)
    status = wizard.set_node_info_role(is_storage, is_iscsi, is_backup)
    if status == Status().done:
        cluster_state = wizard.is_cluster_config_complated()
        if cluster_state:
            node_name = configuration().get_node_name()
            manage_users = ManageUsers()
            stat = manage_users.sync_users(node_name)
        session['success'] = "Node Service Settings Saved"
        session['submitted_page'] = "build_load"
        return redirect(url_for('wizard_controller.main'))
    elif status == Status.error:
        session['err'] = "Error saving node services settings"
        session['submitted_page'] = "node_role_setting"
        return redirect(url_for('wizard_controller.main'), 307)


@wizard_controller.route('/build', methods=['GET'])
def build_cluster():
    if request.method == 'GET':
        try:
            wizerd = Wizard()
            management_urls = []
            tasks_mssages = []

            status = wizerd.build()
            # status = -3
            if status == BuildStatus.done:
                management_urls = wizerd.get_management_urls()

            tasks = wizerd.get_status_reports().failed_tasks
            node_number = wizerd.get_status_reports().nod_num
            for task in tasks:
                msg = gettext(task)
                tasks_mssages.append(msg)
            # tasks_mssages.append("test error1")
            execution_status = executionStatus()
            execution_status.status = status
            execution_status.report_status = tasks_mssages
            execution_status.management_url = management_urls
            execution_status.node_num = node_number
            data = execution_status.write_json()
            return data

        except Exception as e:
            session['err'] = "ui_deploy_build_err_exception"
            logger.error(e)


@wizard_controller.route('/start_network', methods=['POST'])
def start_network_setting():
    if request.method == 'POST':
        try:
            wizard = Wizard()
            status = wizard.start_node_backend_networks()
            if status == Status.error:
                session['err'] = "Error staring node backend networks."
                session['submitted_page'] = "node_summary_setting"
                return redirect(url_for('wizard_controller.main'), 307)
            else:
                session['success'] = "Backend networks started successfully."
                session['submitted_page'] = "build_load"
                return redirect(url_for('wizard_controller.main'))
        except Exception as e:
            session['err'] = "Error starting backend networks."
            logger.error(e)


@wizard_controller.route('/cluster_interface_setting/save', methods=['POST'])
def save_cluster_interface_setting():
    if request.method == 'POST':
        try:

            jumbo_frames_interfaces = []
            final_bonded_interfaces = []
            deployment_data = session['deployment_data']
            deployment_data['cluster_NIC_settings']['jumbo_frames'] = False
            deployment_data['cluster_NIC_settings']['NIC_bonding'] = False
            if request.form['frame_size'] == "jumbo_frames":
                deployment_data['cluster_NIC_settings']['jumbo_frames'] = True
                for jf_interface in request.form.getlist('jf_interface[]'):
                    jumbo_frames_interfaces.append(jf_interface)
                deployment_data['cluster_NIC_settings']['jf_interfaces'] = jumbo_frames_interfaces

            if request.form['interface_type'] == "bond":
                bonded_interfaces = json.loads(request.form['bonded_NIC'])
                deployment_data['cluster_NIC_settings']['NIC_bonding'] = True
                deployment_data['cluster_NIC_settings']['bonded_interfaces_list'] = []
                for bond_interface in bonded_interfaces:
                    new_bond = Bond()
                    new_bond.load_json(json.dumps(bond_interface))
                    final_bonded_interfaces.append(new_bond)
                    interface_list = bond_interface['interfaces'].split(",")
                    if all(item in jumbo_frames_interfaces for item in interface_list):
                        bond_interface['is_jumbo_frames'] = True

                    # add all bonded interfacesto one list
                    bond_list = bond_interface["interfaces"].split(",")
                    deployment_data['cluster_NIC_settings']['bonded_interfaces_list'].extend(bond_list)
                    deployment_data['cluster_NIC_settings']['bonded_interfaces'] = bonded_interfaces
            session['deployment_data'] = deployment_data
            session['keep_data'] = True
            if not jumbo_frames_interfaces:
                deployment_data['cluster_NIC_settings']['jf_interfaces'] = []
                jf_flag = False
            else:
                jf_flag = True

            if not final_bonded_interfaces:
                deployment_data['cluster_NIC_settings']['bonded_interfaces'] = []
                bond_flag = False
            else:
                bond_flag = True

            if bond_flag:
                if jf_flag:
                    new_wizard = Wizard()
                    status = new_wizard.set_cluster_interface(final_bonded_interfaces, jumbo_frames_interfaces)
                    if status == Status.done:
                        session['success'] = "ui_deploy_save_cluster_interface_setting_success"
                        deployment_data['cluster_NIC_settings']['success_msg'] = session['success']
                        session['submitted_page'] = "cluster_network_setting"
                        return redirect(url_for('wizard_controller.main'))
                    elif status == Status.error:
                        session['error'] = "ui_deploy_save_cluster_interface_setting_error"
                        session['submitted_page'] = "cluster_interface_setting"
                        return redirect(url_for('wizard_controller.main'), 307)
                elif not jf_flag:
                    new_wizard = Wizard()
                    status = new_wizard.set_cluster_interface(final_bonded_interfaces, jumbo_frames_interfaces)
                    if status == Status.done:
                        session['success'] = "ui_deploy_save_cluster_interface_setting_success"
                        deployment_data['cluster_NIC_settings']['success_msg'] = session['success']
                        session['submitted_page'] = "cluster_network_setting"
                        return redirect(url_for('wizard_controller.main'))
                    elif status == Status.error:
                        session['error'] = "error while saving cluster interface"
                        session['submitted_page'] = "cluster_interface_setting"
                        return redirect(url_for('wizard_controller.main'), 307)
            elif not bond_flag:
                if jf_flag:
                    new_wizard = Wizard()
                    status = new_wizard.set_cluster_interface(final_bonded_interfaces, jumbo_frames_interfaces)
                    if status == Status.done:
                        session['success'] = "ui_deploy_save_cluster_interface_setting_success"
                        deployment_data['cluster_NIC_settings']['success_msg'] = session['success']
                        session['submitted_page'] = "cluster_network_setting"
                        return redirect(url_for('wizard_controller.main'))
                    elif status == Status.error:
                        session['error'] = "ui_deploy_save_cluster_interface_setting_error"
                        session['submitted_page'] = "cluster_interface_setting"
                        return redirect(url_for('wizard_controller.main'), 307)
                elif not jf_flag:
                    new_wizard = Wizard()
                    new_wizard.reset_cluster_interface()
                    session['submitted_page'] = "cluster_network_setting"
                    return redirect(url_for('wizard_controller.main'))
        except Exception as e:
            session['err'] = "ui_deploy_save_cluster_interface_setting_error"
            session['submitted_page'] = "cluster_interface_setting"
            return redirect(url_for('wizard_controller.main'), 307)


@wizard_controller.route('/back_cluster_interface_setting/save', methods=['POST'])
def back_to_cluster_interface_setting():
    if request.method == 'POST':
        try:
            deployment_data = session['deployment_data']
            session['success'] = deployment_data['cluster_info_&_join']['success_msg']
            session['submitted_page'] = "cluster_interface_setting"
            session['keep_data'] = True
            return redirect(url_for('wizard_controller.main'))
        except Exception as e:
            logger.error(e)
            return redirect(url_for('wizard_controller.main'), 307)


@wizard_controller.route('/state', methods=['GET'])
def state():
    try:
        StateUtil().collect_local_node_state()
        node_name = configuration().get_node_name()
        collected_path = ConfigAPI().get_collect_state_dir() + node_name + '.tar'
        manage_node = ManageNode()
        return Response(stream_with_context(manage_node.read_file(collected_path)), mimetype="application/x-tar",
                        headers={"Content-Disposition": "attachment; filename={}".format(node_name + '.tar')})
    except Exception as e:
        logger.exception("error download state file")


@wizard_controller.route('/state_all', methods=['GET'])
def state_all():
    try:
        StateUtil().collect_all()
        cluster_name = configuration().get_cluster_name()
        cluster_file = '/opt/petasan/log/' + cluster_name + '.tar'
        manage_node = ManageNode()
        return Response(stream_with_context(manage_node.read_file(cluster_file)), mimetype="application/x-tar",
                        headers={"Content-Disposition": "attachment; filename={}".format(cluster_name + '.tar')})
    except Exception as e:
        logger.exception("error download state all file")


@wizard_controller.route('/get_tuning_template/<template_name>', methods=['GET'])
def get_tuning_template_settings(template_name):
    template_config = configuration().get_template(template_name)
    json_data = json.dumps(template_config)
    return json_data


@wizard_controller.route('/save_tuning_temlplate', methods=['POST'])
def save_cluster_tuning_template():
    try:
        if request.method == 'POST':
            ceph_config = request.form['ceph_script']
            lio_config = request.form['lio_script']
            post_script_config = request.form['post_deploy_script']

            ceph_config_final = '\n'.join(ceph_config.splitlines())
            lio_config_final = '\n'.join(lio_config.splitlines())
            post_script_config_final = '\n'.join(post_script_config.splitlines())

            cluster_size = request.form['cluster_size']
            replicas_no = request.form['replicas_no']
            storage_engine = request.form['storage_engine']

            ceph_cluster_size = "osd_pool_default_pg_num =  " + `int(
                cluster_size)` + '\n' + "osd_pool_default_pgp_num = " + `int(cluster_size)` + '\n'
            ceph_replicas_no = "osd_pool_default_size =  " + `int(
                replicas_no)` + '\n' + "osd_pool_default_min_size = " + `int(replicas_no) - 1` + '\n'
            ceph_rest_config = '[global]\n' + ceph_cluster_size + ceph_replicas_no
            final_ceph_config = ceph_config_final.replace('[global]', ceph_rest_config)

            # save cluster tuning in deploy_data dict for previous button
            deployment_data = session['deployment_data']
            deployment_data['cluster_tuning']['cluster_size'] = cluster_size
            deployment_data['cluster_tuning']['replicas_no'] = replicas_no
            deployment_data['cluster_tuning']['storage_engine'] = storage_engine
            deployment_data['cluster_tuning']['tuning_template'] = request.form['tuning_template']
            deployment_data['cluster_tuning']['ceph_script'] = ceph_config
            deployment_data['cluster_tuning']['lio_config'] = lio_config
            deployment_data['cluster_tuning']['post_script_config'] = post_script_config
            session['deployment_data'] = deployment_data
            session['keep_data'] = True

            configuration().save_current_tunings(final_ceph_config, lio_config_final, post_script_config_final,
                                                 storage_engine)

            session['success'] = "ui_deploy_save_cluster_tuning_setting_succ"
            deployment_data['cluster_tuning']['success_msg'] = session['success']
            session['submitted_page'] = "node_network_setting"
            session['join'] = "join"
            session['come_from'] = "tuning"
            return redirect(url_for('wizard_controller.main'))

    except Exception as e:
        session['err'] = "ui_deploy_save_cluster_tuning_setting_error"
        session['submitted_page'] = "tuning_form"
        return redirect(url_for('wizard_controller.main'), 307)


@wizard_controller.route('/back_save_tuning_temlplate', methods=['POST'])
def back_to_cluster_tuning():
    if request.method == 'POST':
        try:
            deployment_data = session['deployment_data']
            session['success'] = deployment_data['cluster_network_sittings']['success_msg']
            session['submitted_page'] = "tuning_form"
            session['keep_data'] = True
            return redirect(url_for('wizard_controller.main'))
        except Exception as e:
            logger.error(e)
            return redirect(url_for('wizard_controller.main'), 307)

@wizard_controller.route('/reset', methods=['POST'])
def reset_wizard():
    if request.method == 'POST':
        try:
            if 'deployment_data' in session:
                session.pop('deployment_data')
            if 'keep_data' in session:
                session.pop('keep_data')
            if 'submitted_page' in session:
                session.pop('submitted_page')
            return redirect(url_for('wizard_controller.main'))
        except Exception as e:
            logger.error(e)
            return redirect(url_for('wizard_controller.main'), 307)

