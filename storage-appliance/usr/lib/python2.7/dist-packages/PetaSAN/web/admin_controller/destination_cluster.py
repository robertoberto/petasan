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

from PetaSAN.core.entity.models.destination_cluster import DestinationCluster
from PetaSAN.backend.replication.manage_destination_cluster import ManageDestinationCluster
from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.core.common.CustomException import ConsulException, ReplicationException
from PetaSAN.core.common.log import logger

destination_cluster_controller = Blueprint('destination_cluster_controller', __name__)

list_err = "err"
list_warning = "warning"
list_success = "success"
result = ""


@destination_cluster_controller.route('/replication/destination_clusters/list', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationClusters')
def dest_clusters_list():
    if request.method == 'GET' or request.method == 'POST':

        try:
            manage_dest_cluster = ManageDestinationCluster()
            dest_cluster_list = manage_dest_cluster.get_replication_dest_clusters()

            if list_err in session:

                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/destination_clusters/view_dest_clusters.html',
                                       dest_cluster_list=dest_cluster_list, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('/admin/replication/destination_clusters/view_dest_clusters.html',
                                       dest_cluster_list=dest_cluster_list, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('/replication/destination_clusters/view_dest_clusters.html',
                                       dest_cluster_list=dest_cluster_list, warning=result)

            else:
                return render_template('/admin/replication/destination_clusters/view_dest_clusters.html',
                                       dest_cluster_list=dest_cluster_list)


        except ConsulException as e:
            logger.error(e)
            if e.id == ConsulException.GENERAL_EXCEPTION:
                result = session['err'] = "core_consul_exception_cant_get_dest_clusters"
                return render_template('/admin/replication/destination_clusters/view_dest_clusters.html', err=result)

        except Exception as e:
            result = session['err'] = "core_exception_cant_get_dest_clusters"
            logger.error(e)
            return render_template('/admin/replication/destination_clusters/view_dest_clusters.html', err=result)


@destination_cluster_controller.route('/replication/destination_clusters/list/view/<cluster_name>',
                                      methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationClusters')
def view_dest_cluster(cluster_name):
    if request.method == 'GET' or request.method == 'POST':

        try:
            manage_dest_cluster = ManageDestinationCluster()
            selected_dest_cluster = manage_dest_cluster.get_replication_dest_cluster(cluster_name)

            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('admin/replication/destination_clusters/edit_dest_cluster.html',
                                       selected_dest_cluster=selected_dest_cluster, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('admin/replication/destination_clusters/edit_dest_cluster.html',
                                       selected_dest_cluster=selected_dest_cluster, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('admin/replication/destination_clusters/edit_dest_cluster.html',
                                       selected_dest_cluster=selected_dest_cluster, warning=result)

            else:
                return render_template('admin/replication/destination_clusters/edit_dest_cluster.html',
                                       selected_dest_cluster=selected_dest_cluster)

        except Exception as e:
            result = session['err'] = "ui_admin_view_get_dest_cluster_info_error"
            logger.error(e)
            return render_template('admin/replication/destination_clusters/edit_dest_cluster.html', err=result,
                                   selected_dest_cluster=selected_dest_cluster)


@destination_cluster_controller.route('/replication/destination_clusters/list/edit/<cluster_name>',
                                      methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationClusters')
def edit_dest_cluster(cluster_name):
    if request.method == 'GET' or request.method == 'POST':
        mesg_err = ""
        mesg_success = ""
        mesg_warning = ""
        try:
            # get selected destination cluster
            manage_dest_cluster = ManageDestinationCluster()
            selected_dest_cluster = manage_dest_cluster.get_replication_dest_cluster(cluster_name)

            # get destination Cluster from html form.
            remote_ip = request.form['dest_cluster_ip']
            ssh_private_key = str(request.form['key'])
            user_name = request.form['userName']

            # fill destination Cluster entity .
            selected_dest_cluster.remote_ip = remote_ip
            selected_dest_cluster.ssh_private_key = ssh_private_key
            selected_dest_cluster.user_name = user_name

            # send job entity to the backend to be saved in the consul.
            manage_dest_cluster = ManageDestinationCluster()
            manage_dest_cluster.edit_destination_cluster(selected_dest_cluster)
            session['success'] = "ui_admin_edit_dest_cluster_success"
            return redirect(url_for('destination_cluster_controller.dest_clusters_list'))

        except Exception as e:
            logger.error(e)
            session['err'] = "ui_admin_edit_dest_cluster_error"
            return redirect(url_for('destination_cluster_controller.view_dest_cluster', cluster_name=cluster_name))


@destination_cluster_controller.route('/replication/destination_clusters/list/add', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationClusters')
def add_dest_cluster():
    if request.method == 'GET' or request.method == 'POST':
        try:
            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/destination_clusters/add_dest_cluster.html', err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('/admin/replication/destination_clusters/add_dest_cluster.html', success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('/admin/replication/destination_clusters/add_dest_cluster.html', warning=result)

            else:
                return render_template('/admin/replication/destination_clusters/add_dest_cluster.html')


        except Exception as e:
            session['err'] = "ui_admin_add_dest_cluster_error"
            logger.error(e)
            return redirect(url_for('destination_cluster_controller.dest_clusters_list'))


@destination_cluster_controller.route('/replication/destination_clusters/list/save', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationClusters')
def save_dest_cluster():
    if request.method == 'GET' or request.method == 'POST':
        mesg_err = ""
        mesg_success = ""
        mesg_warning = ""
        try:
            # get destination Cluster from html form.
            cluster_name = request.form['cluster_name']
            remote_ip = request.form['dest_cluster_ip']
            ssh_private_key = str(request.form['key'])
            user_name = request.form['userName']

            # fill destination Cluster entity .
            dest_cluster = DestinationCluster()
            dest_cluster.cluster_name = cluster_name
            dest_cluster.remote_ip = remote_ip
            dest_cluster.ssh_private_key = ssh_private_key
            dest_cluster.user_name = user_name

            # send job entity to the backend to be saved in the consul.
            manage_dest_cluster = ManageDestinationCluster()
            manage_dest_cluster.add_destination_cluster(dest_cluster)
            session['success'] = "ui_admin_add_dest_cluster_success"
            return redirect(url_for('destination_cluster_controller.dest_clusters_list'))

        except ReplicationException as e:
            logger.error(e)
            if e.id == ReplicationException.DESTINATION_CLUSTER_EXIST:
                session['err'] = "ui_admin_add_dest_cluster_duplicate_err"
                return redirect(url_for('destination_cluster_controller.add_dest_cluster'))

            elif e.id == ReplicationException.PERMISSION_DENIED:
                session['err'] = "ui_admin_add_dest_cluster_permission_denied"
                return redirect(url_for('destination_cluster_controller.add_dest_cluster'))

            elif e.id == ReplicationException.WRONG_CLUSTER_NAME:
                session['err'] = "ui_admin_add_dest_cluster_cluster_name_err"
                return redirect(url_for('destination_cluster_controller.add_dest_cluster'))

        except Exception as e:
            logger.error(e)
            session['err'] = "ui_admin_add_dest_cluster_error"
            return redirect(url_for('destination_cluster_controller.add_dest_cluster'))


@destination_cluster_controller.route('/replication/destination_clusters/delete/<cluster_name>',
                                      methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationClusters')
def delete_dest_cluster(cluster_name):
    if request.method == 'GET' or request.method == 'POST':
        try:
            # get selected destination cluster
            manage_dest_cluster = ManageDestinationCluster()
            selected_dest_cluster = manage_dest_cluster.get_replication_dest_cluster(cluster_name)
            manage_dest_cluster.delete_replication_dest_cluster(selected_dest_cluster)

            session["success"] = "ui_admin_delete_dest_cluster_success"
            return redirect(url_for('destination_cluster_controller.dest_clusters_list'))

        except ReplicationException as e:
            logger.error(e)
            if e.id == ReplicationException.DESTINATION_CLUSTER_USED_IN_REPLICATION:
                session['err'] = "ui_admin_add_dest_cluster_used_err"
                return redirect(url_for('destination_cluster_controller.dest_clusters_list'))

        except Exception as e:
            session['err'] = "ui_admin_delete_dest_cluster_error"
            logger.error(e)
            return redirect(url_for('destination_cluster_controller.dest_clusters_list'))


@destination_cluster_controller.route('/replication/destination_clusters/details/<cluster_name>',
                                      methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationClusters')
def view_dest_cluster_details(cluster_name):
    if request.method == 'GET' or request.method == 'POST':
        try:

            manage_dest_cluster = ManageDestinationCluster()
            selected_dest_cluster = manage_dest_cluster.get_replication_dest_cluster(cluster_name)
            json_data = json.dumps(selected_dest_cluster.__dict__, sort_keys=True)
            return json_data

        except Exception as e:
            session['err'] = "ui_admin_view_dest_cluster_details_error"
            result = session['err']
            logger.error(e)
            return redirect(url_for('destination_cluster_controller.dest_clusters_list'))


@destination_cluster_controller.route('/replication/destination_clusters/test', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationClusters')
def test_connection():
    if request.method == 'GET' or request.method == 'POST':
        mesg_err = ""
        mesg_success = ""
        mesg_warning = ""
        test_flag = False
        try:
            # get destination Cluster from html form.
            cluster_name = request.values['cluster_name']
            user_name = request.values['userName']
            remote_ip = request.values['dest_cluster_ip']
            ssh_private_key = str(request.values['key'])

            # fill destination Cluster entity .
            dest_cluster = DestinationCluster()
            dest_cluster.cluster_name = cluster_name
            dest_cluster.remote_ip = remote_ip
            dest_cluster.ssh_private_key = ssh_private_key
            dest_cluster.user_name = user_name

            mng_dest_cluster = ManageDestinationCluster()
            dest_cluster.cluster_fsid = mng_dest_cluster.get_dest_cluster_fsid(dest_cluster)
            print(dest_cluster.cluster_fsid)

            if dest_cluster.cluster_fsid and len(dest_cluster.cluster_fsid) > 0 :
                test_flag = True

            if "err" in session:
                mesg_err = session["err"]
                session.pop("err")
            elif "success" in session:
                mesg_success = session["success"]
                session.pop("success")
            elif "warning" in session:
                mesg_warning = session["warning"]
                session.pop("warning")
            json_data = json.dumps(test_flag)
            return json_data

        except Exception as e:
            logger.error(e)
            mesg_err = "error in loading page"
        return render_template('/admin/replication/destination_clusters/add_dest_cluster.html', err=mesg_err,
                               success=mesg_success, warning=mesg_warning)
