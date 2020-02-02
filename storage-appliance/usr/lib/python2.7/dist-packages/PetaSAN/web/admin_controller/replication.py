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
import json
from PetaSAN.backend.replication.manage_destination_cluster import ManageDestinationCluster
from PetaSAN.core.common.messages import gettext
from PetaSAN.core.entity.disk_info import DiskMeta
from PetaSAN.core.entity.models.replication_job import ReplicationJob
from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.core.common.CustomException import ConsulException, CephException, ReplicationException
from PetaSAN.core.common.log import logger
from PetaSAN.core.cluster.configuration import configuration
from PetaSAN.backend.manage_replication_jobs import ManageReplicationJobs
from PetaSAN.backend.replication.manage_remote_replication import ManageRemoteReplication
from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.backend.manage_node import ManageNode
from PetaSAN.backend.replication.replication_handler import ReplicationHandler

replication_controller = Blueprint('replication_controller', __name__)

list_err = "err"
list_warning = "warning"
list_success = "success"


@replication_controller.route('/replication/job_list', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def job_list():
    """
    DOCSTRING : this function gets ( all the replication jobs ) then render to the page :
    'admin/replication/job_list.html'.
    Args : None
    Returns : render to the template page : 'admin/replication/job_list.html'
    """
    if request.method == 'GET' or request.method == 'POST':
        try:
            manage_replication = ManageReplicationJobs()
            jobs_dict = manage_replication.get_replication_jobs()

            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/job_list.html', jobs_dict=jobs_dict, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('/admin/replication/job_list.html', jobs_dict=jobs_dict, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('/admin/replication/job_list.html', jobs_dict=jobs_dict, warning=result)

            else:
                return render_template('/admin/replication/job_list.html', jobs_dict=jobs_dict)


        except ConsulException as e:
            logger.error(e)
            if e.id == ConsulException.CONNECTION_TIMEOUT:
                result = session['err'] = "ui_admin_login_consul_connection_error"
                return render_template('/admin/replication/job_list.html', err=result)

            if e.id == ConsulException.GENERAL_EXCEPTION:
                result = session['err'] = "core_consul_exception_cant_get_rep_jobs"
                return render_template('/admin/replication/job_list.html', err=result)

        except Exception as e:
            result = session['err'] = "core_exception_cant_get_rep_jobs"
            logger.error(e)
            return render_template('/admin/replication/job_list.html', err=result)


@requires_auth
@authorization("ReplicationJobs")
def get_selected_Job_info(job_id):
    """
    DOCSTRING : this function gets the Replication Job Entity by its job_id ...
    Args : job_id (string)
    Returns : The return value is (ReplicationJob) Entity.
    """
    manage_replication = ManageReplicationJobs()
    replication_job = manage_replication.get_replication_job(job_id)
    return replication_job


@replication_controller.route('/replication/get_job/<job_id>', methods=['GET', 'POST'])
@requires_auth
@authorization("ReplicationJobs")
def get_selected_Job(job_id):
    """
    DOCSTRING : this function gets the schedule of selected replication job ...
    Args : job_id (string)
    Returns : replication job schedule .
    """
    replication_job = get_selected_Job_info(job_id)
    schedule = json.dumps \
        (replication_job.schedule)
    return schedule


@replication_controller.route('/replication/start/<job_id>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def start_job(job_id):
    """
    DOCSTRING : this function starts the Replication Job ( add replication job to Cron jobs ) ...
    Args : job_id (string)
    Returns : return to page : 'admin/replication/job_list.html'
    """
    if request.method == 'GET' or request.method == 'POST':
        try:
            manage_replication = ManageReplicationJobs()

            # Get job by job_id:
            replication_job = get_selected_Job_info(job_id)

            # Start job:
            if replication_job:
                manage_replication.start_replication_job(replication_job)
                return redirect(url_for('replication_controller.job_list'))

            # else:
            #     result = session['err'] = "core_exception_cant_start_rep_job"
            #     return render_template('/admin/replication/job_list.html', err=result)

        except ConsulException as e:
            logger.error(e)
            if e.id == ConsulException.GENERAL_EXCEPTION:
                session['err'] = "core_exception_cant_start_rep_job"
                return redirect(url_for('replication_controller.job_list'))

        except ReplicationException as e:
            logger.error(e)
            if e.id == ReplicationException.CONNECTION_TIMEOUT:
                session['err'] = "Connection Timeout."
                return redirect(url_for('replication_controller.job_list'))

            elif e.id == ReplicationException.CONNECTION_REFUSED:
                session['err'] = "Connection Refused."
                return redirect(url_for('replication_controller.job_list'))

            elif e.id == ReplicationException.PERMISSION_DENIED:
                session['err'] = "Permission Denied."
                return redirect(url_for('replication_controller.job_list'))

            elif e.id == ReplicationException.GENERAL_EXCEPTION:
                session['err'] = "core_exception_cant_start_rep_job"
                return redirect(url_for('replication_controller.job_list'))

        except Exception as e:
            session['err'] = "core_exception_cant_start_rep_job"
            logger.error(e)
            return redirect(url_for('replication_controller.job_list'))


@replication_controller.route('/replication/stop/<job_id>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def stop_job(job_id):
    """
    DOCSTRING : this function stops the Replication Job ( remove replication job from Cron jobs ) ...
    Args : job_id (string)
    Returns : return to page : 'admin/replication/job_list.html'
    """
    if request.method == 'GET' or request.method == 'POST':
        try:
            manage_replication = ManageReplicationJobs()

            # Get job by job_id:
            replication_job = get_selected_Job_info(job_id)

            # Stop job:
            if replication_job:
                manage_replication.stop_replication_job(replication_job)
                return redirect(url_for('replication_controller.job_list'))

            # else:
            #     result = session['err'] = "core_exception_cant_stop_rep_job"
            #     return render_template('/admin/replication/job_list.html', err=result)

        except ConsulException as e:
            logger.error(e)
            if e.id == ConsulException.GENERAL_EXCEPTION:
                session['err'] = "core_consul_exception_cant_stop_rep_job"
                return redirect(url_for('replication_controller.job_list'))

        except ReplicationException as e:
            logger.error(e)
            if e.id == ReplicationException.CONNECTION_TIMEOUT:
                session['err'] = "Connection Timeout."
                return redirect(url_for('replication_controller.job_list'))

            elif e.id == ReplicationException.CONNECTION_REFUSED:
                session['err'] = "Connection Refused."
                return redirect(url_for('replication_controller.job_list'))

            elif e.id == ReplicationException.PERMISSION_DENIED:
                session['err'] = "Permission Denied."
                return redirect(url_for('replication_controller.job_list'))

            elif e.id == ReplicationException.GENERAL_EXCEPTION:
                session['err'] = "core_consul_exception_cant_stop_rep_job"
                return redirect(url_for('replication_controller.job_list'))

        except Exception as e:
            session['err'] = "core_exception_cant_stop_rep_job"
            logger.error(e)
            return redirect(url_for('replication_controller.job_list'))


@replication_controller.route('/replication/delete/<job_id>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def delete_job(job_id):
    """
    DOCSTRING : this function is called to delete a certain replication job , then redirect to the page :
    'admin/replication/job_list.html'.
    Args : pool_name (string)
    Returns : returns to the page : 'admin/replication/job_list.html'
    """
    if request.method == 'GET' or request.method == 'POST':
        try:
            manage_replication = ManageReplicationJobs()

            # Get job by job_id:
            replication_job = get_selected_Job_info(job_id)

            # Stop job:
            if replication_job:
                manage_replication.delete_replication_job(replication_job)
                return redirect(url_for('replication_controller.job_list'))

            # else:
            #     result = session['err'] = "core_exception_cant_delete_rep_job"
            #     return redirect(url_for('replication_controller.job_list'))

        except ConsulException as e:
            logger.error(e)
            if e.id == ConsulException.GENERAL_EXCEPTION:
                session['err'] = "core_exception_cant_delete_rep_job"
                return redirect(url_for('replication_controller.job_list'))

        except ReplicationException as e:
            logger.error(e)
            if e.id == ReplicationException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_add_job_connction_timeout_err"
                return redirect(url_for('replication_controller.job_list'))

            elif e.id == ReplicationException.CONNECTION_REFUSED:
                session['err'] = "ui_admin_add_job_connction_refused_err"
                return redirect(url_for('replication_controller.job_list'))

            elif e.id == ReplicationException.PERMISSION_DENIED:
                session['err'] = "Permission Denied."
                return redirect(url_for('replication_controller.job_list'))

            elif e.id == ReplicationException.GENERAL_EXCEPTION:
                session['err'] = "core_consul_exception_cant_delete_rep_job"
                return redirect(url_for('replication_controller.job_list'))

        except Exception as e:
            session['err'] = "core_consul_exception_cant_delete_rep_job"
            logger.error(e)
            return redirect(url_for('replication_controller.job_list'))


@replication_controller.route('/replication/add_job', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def add_job():
    """
    DOCSTRING : this function is called when opening the Add new replication job form page.
    Args : None
    Returns : render to the template page : 'admin/replication/add_replication_job.html'
    """
    if request.method == 'GET' or request.method == 'POST':
        try:
            backup_nodes = []
            destination_clusters_list = []
            manage_node = ManageNode()
            nodes = manage_node.get_node_list()
            cluster_name = configuration().get_cluster_name(custom_name=True)
            manage_destination_cluster = ManageDestinationCluster()
            destination_clusters_dict = manage_destination_cluster.get_replication_dest_clusters()
            for dest_cluster in destination_clusters_dict:
                destination_clusters_list.append(dest_cluster)
            destination_clusters_list.sort()
            for node in nodes:
                if node.is_backup:
                    backup_nodes.append(node)
            backup_nodes.sort()

            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('/admin/replication/add_replication_job.html', backup_nodes=backup_nodes,
                                       cluster_name=cluster_name, destination_clusters_list=destination_clusters_list,
                                       err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('/admin/replication/add_replication_job.html', backup_nodes=backup_nodes,
                                       cluster_name=cluster_name, destination_clusters_list=destination_clusters_list,
                                       success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('/admin/replication/add_replication_job.html', backup_nodes=backup_nodes,
                                       cluster_name=cluster_name, destination_clusters_list=destination_clusters_list,
                                       warning=result)

            else:
                return render_template('/admin/replication/add_replication_job.html', backup_nodes=backup_nodes,
                                       cluster_name=cluster_name, destination_clusters_list=destination_clusters_list)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return redirect(url_for('replication_controller.job_list'))

        except Exception as e:
            session['err'] = "ui_admin_add_job_error"
            logger.error(e)
            return redirect(url_for('replication_controller.job_list'))


@replication_controller.route('/replication/source_disks', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def get_disks_list():
    """
    DOCSTRING : this function is called to get all source cluster images.
    Args : None
    Returns : List of all source images.
    """
    mesg_err = ""
    mesg_success = ""
    mesg_warning = ""

    try:
        disks = []
        manage_disk = ManageDisk()
        available_disk_list = manage_disk.get_disks_meta()

        for obj in available_disk_list:
            disks.append(obj.__dict__)

        if "err" in session:
            mesg_err = session["err"]
            session.pop("err")

        elif "success" in session:
            mesg_success = session["success"]
            session.pop("success")

        elif "warning" in session:
            mesg_warning = session["warning"]
            session.pop("warning")

        json_data = json.dumps(disks)
        return json_data

    except Exception as e:
        logger.error(e)
        mesg_err = "error in loading page"
    return render_template('/admin/replication/add_replication_job.html', err=mesg_err,
                           success=mesg_success, warning=mesg_warning)


@replication_controller.route('/replication/destination_disks', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def get_replicated_disks():
    """
    DOCSTRING : this function is called to get all destination cluster images.
    Args : None
    Returns : List of all destination images.
    """
    if request.method == 'GET' or request.method == 'POST':
        mesg_err = ""
        mesg_success = ""
        mesg_warning = ""

        try:
            # Get data from destination cluster:
            dest_cluster_name = request.values['cluster_name']
            manage_remote_replication = ManageRemoteReplication()
            manage_remote_replication.cluster_name = dest_cluster_name
            dest_disks_lis = manage_remote_replication.get_replicated_disks_list

            if "err" in session:
                mesg_err = session["err"]
                session.pop("err")

            elif "success" in session:
                mesg_success = session["success"]
                session.pop("success")

            elif "warning" in session:
                mesg_warning = session["warning"]
                session.pop("warning")

            json_data = json.dumps(dest_disks_lis)
            return json_data

        except ReplicationException as e:
            if e.id == ReplicationException.CONNECTION_REFUSED:
                result = gettext("ui_admin_add_job_connction_refused_err")
            elif e.id == ReplicationException.CONNECTION_TIMEOUT:
                result = gettext("ui_admin_add_job_connction_timeout_err")
            elif e.id == ReplicationException.PERMISSION_DENIED:
                result = gettext("ui_admin_add_dest_cluster_permission_denied")
            else:
                result = gettext("ui_admin_get_rep_disk_list")
            logger.error(e)
            err = {"err":result}
            result = json.dumps(err)
            return result

        except Exception as e:
            result =  gettext("ui_admin_add_job_connction_timeout_err")
            result = json.dumps(result)
            logger.error(e)
            err = {"err":result}
            result = json.dumps(err)
            return result


@replication_controller.route('/replication/save_job', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def save_job():
    """
    DOCSTRING : this function is called at saving a new replication job , if saving operation is succeeded it renders to the
    template page : 'admin/replication/job_list.html' with a success message , and if not it redirects
    to : 'admin/replication/add_replication_job.html' with an error message ...
    Args : None
    Returns : in success , it renders to : 'admin/replication/job_list.html' with a success message
    in failure , it redirects to : 'admin/replication/add_replication_job.html'
    """
    if request.method == 'GET' or request.method == 'POST':
        mesg_err = ""
        mesg_success = ""
        mesg_warning = ""

        try:
            replication_job = ReplicationJob()
            local_replication = ReplicationHandler()
            remote_replication = ManageRemoteReplication()
            manage_replication = ManageReplicationJobs()

            # get replication job from html form.
            job_name = request.form['job_name']
            schedule_object = json.loads(request.form['schedule_object'])
            backup_node = request.form['backup_node']
            source_disk = request.form['source_disk']
            source_cluster_name = request.form['source_cluster']
            dest_cluster_name = request.form['dest_cluster_name']
            destination_disk = request.form['destination_disk']
            rep_compression_mode = request.form['rep_compression_mode']

            if rep_compression_mode == 'enabled':
                rep_compression_algorithm = request.form['rep_compression_algorithm']
                replication_job.compression_algorithm = rep_compression_algorithm

            pre_snap_script = request.form['pre_snap_script']
            post_snap_script = request.form['post_snap_script']
            post_job_complete = request.form['post_job_complete']

            src_disk_meta = manage_replication.get_src_disk_meta(source_disk)
            remote_replication.disk_id = destination_disk
            remote_replication.cluster_name = dest_cluster_name
            dest_disk_meta_dict = remote_replication.get_disk_meta()
            dest_disk_meta_obj = DiskMeta(dest_disk_meta_dict)

            # check if both source and destination disks have the same size.
            if src_disk_meta.size != dest_disk_meta_obj.size:
                session['err'] = "ui_admin_add_job_error_scr_dest_size_mismatch"
                return redirect(url_for('replication_controller.add_job'))
            if src_disk_meta.replication_info or dest_disk_meta_obj.replication_info:
                session['err'] = "ui_admin_add_job_error_scr_dest_have_replication_info"
                return redirect(url_for('replication_controller.add_job'))

            # fill replication job entity .
            replication_job.job_name = job_name
            replication_job.schedule = schedule_object
            replication_job.node_name = backup_node
            replication_job.source_cluster_name = source_cluster_name
            replication_job.source_disk_id = source_disk
            replication_job.destination_disk_id = destination_disk
            replication_job.destination_cluster_name = dest_cluster_name
            replication_job.pre_snap_url = pre_snap_script
            replication_job.post_snap_url = post_snap_script
            replication_job.post_job_complete = post_job_complete

            # update src and dest disk meta.replication_info.
            replication_info = {
                'src_disk_id': replication_job.source_disk_id,
                'src_disk_name': src_disk_meta.disk_name,
                'src_cluster_fsid': "",
                'src_cluster_name': replication_job.source_cluster_name,
                'dest_disk_id': replication_job.destination_disk_id,
                'dest_disk_name': dest_disk_meta_obj.disk_name,
                'dest_cluster_name': replication_job.destination_cluster_name,
                'dest_cluster_ip': "",
                'dest_cluster_fsid': ""
            }
            src_disk_meta.replication_info = replication_info

            # send job entity to the backend to be saved in the consul.
            manage_replication.add_replication_job(replication_job, src_disk_meta)
            session['success'] = "ui_admin_add_job_success"
            return redirect(url_for('replication_controller.job_list'))

        except ReplicationException as e:
            logger.error(e)
            if e.id == ReplicationException.CONNECTION_REFUSED:
                session['err'] = "ui_admin_add_job_connction_refused_err"
                return redirect(url_for('replication_controller.add_job'))

            elif e.id == ReplicationException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_add_job_connction_timeout_err"
                return redirect(url_for('replication_controller.add_job'))

            elif e.id == ReplicationException.DUPLICATE_NAME:
                session['err'] = "ui_admin_add_job_duplicate_err"
                return redirect(url_for('replication_controller.add_job'))

            elif e.id == ReplicationException.PERMISSION_DENIED:
                session['err'] = "Permission Denied."
                return redirect(url_for('replication_controller.add_job'))

            elif e.id == ReplicationException.GENERAL_EXCEPTION:
                session['err'] = "core_consul_exception_cant_add_rep_job"
                return redirect(url_for('replication_controller.add_job'))

        except Exception as e:
            logger.error(e)
            session['err'] = "ui_admin_add_job_error"
            return redirect(url_for('replication_controller.add_job'))


@replication_controller.route('/replication/job_name/<job_name>/show_logs/<job_id>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def view_job_log(job_name, job_id):
    """
    DOCSTRING : this function is called to show the log of certain replication job.
    Args : job_name (string)  ,  job_id (string)
    Returns : renders to the page : 'admin/replication/show_log.html'
    """
    mesg_err = ""
    mesg_success = ""
    mesg_warning = ""
    logs = []

    try:
        if "err" in session:
            mesg_err = session["err"]
            session.pop("err")

            manage_replication = ManageReplicationJobs()
            job_logs = manage_replication.get_replication_job_log(job_id)

            for log_line in reversed(job_logs):
                logs.append(log_line)
            return render_template('admin/replication/show_log.html', job_name=job_name, job_id=job_id, err=mesg_err,
                                   logs=logs)

        elif "success" in session:
            mesg_success = session["success"]
            session.pop("success")

            manage_replication = ManageReplicationJobs()
            job_logs = manage_replication.get_replication_job_log(job_id)

            for log_line in reversed(job_logs):
                logs.append(log_line)
            return render_template('admin/replication/show_log.html', job_name=job_name, job_id=job_id,
                                   success=mesg_success, logs=logs)

        elif "warning" in session:
            mesg_warning = session["warning"]
            session.pop("warning")

            manage_replication = ManageReplicationJobs()
            job_logs = manage_replication.get_replication_job_log(job_id)

            for log_line in reversed(job_logs):
                logs.append(log_line)
            return render_template('admin/replication/show_log.html', job_name=job_name, job_id=job_id,
                                   warning=mesg_warning, logs=logs)

        else:
            manage_replication = ManageReplicationJobs()
            job_logs = manage_replication.get_replication_job_log(job_id)

            if len(job_logs) < 1:
                return render_template('admin/replication/show_log.html', job_name=job_name, job_id=job_id, logs=logs)

            for log_line in reversed(job_logs):
                logs.append(log_line)

            return render_template('admin/replication/show_log.html', job_name=job_name, job_id=job_id, logs=logs)

    except Exception as e:
        session['err'] = "ui_job_show_job_log_exep"
        logger.error(e.message)
        return redirect(url_for('replication_controller.job_list'))


@replication_controller.route('/replication/job_name/<job_name>/refresh/show_logs/<job_id>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def refresh_show_log(job_name, job_id):
    """
    DOCSTRING : this function is used to refresh the page of job log to show new added logs.
    Args : job_name (string)  ,  job_id (string)
    Returns : redirects to the page : 'admin/replication/show_log.html'
    """
    return redirect(url_for('replication_controller.view_job_log', job_name=job_name, job_id=job_id))


@replication_controller.route('/replication/view_job/<job_id>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def view_job(job_id):
    """
    DOCSTRING : this function is called when opening the Edit replication job form page.
    Args : job_id
    Returns : render to the template page : 'admin/replication/edit_replication_job.html'
    """
    if request.method == 'GET' or request.method == 'POST':
        try:
            backup_nodes = []
            manage_node = ManageNode()
            nodes = manage_node.get_node_list()
            for node in nodes:
                #node.is_backup = True
                if node.is_backup:
                    backup_nodes.append(node)
            # Get job by job_id:
            replication_job = get_selected_Job_info(job_id)

            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('admin/replication/edit_replication_job.html', selected_job=replication_job,
                                       backup_nodes=backup_nodes, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('admin/replication/edit_replication_job.html', selected_job=replication_job,
                                       backup_nodes=backup_nodes, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('admin/replication/edit_replication_job.html', selected_job=replication_job,
                                       backup_nodes=backup_nodes, warning=result)

            else:
                return render_template('admin/replication/edit_replication_job.html', selected_job=replication_job,
                                       backup_nodes=backup_nodes)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                result = session['err'] = "ui_admin_ceph_time_out"
                return render_template('admin/replication/edit_replication_job.html', err=result)

            elif e.id == CephException.GENERAL_EXCEPTION:
                result = session['err'] = "ui_admin_ceph_general_exception"
                logger.error(e)
                return render_template('admin/replication/edit_replication_job.html', err=result)

            result = session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return render_template('admin/replication/edit_replication_job.html', err=result)

        except Exception as e:
            result = session['err'] = "ui_admin_view_get_job_info_error"
            logger.error(e)
            return render_template('admin/replication/edit_replication_job.html', err=result)


@replication_controller.route('/replication/edit_job/<job_id>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def edit_job(job_id):
    """
    DOCSTRING : this function is called when submit the Edit replication job form page.
    Args : None
    Returns : render to the template page : 'admin/replication/job_list.html'
    """
    if request.method == 'GET' or request.method == 'POST':
        mesg_err = ""
        mesg_success = ""
        mesg_warning = ""

        try:
            local_replication = ReplicationHandler()
            remote_replication = ManageRemoteReplication()
            manage_replication = ManageReplicationJobs()
            replication_job = get_selected_Job_info(job_id)
            old_node = replication_job.node_name

            job_name = request.form['job_name']
            schedule = str((request.form['schedule_object']))
            schedule_object = eval(schedule)
            backup_node = request.form['backup_node']
            source_cluster_name = request.form['source_cluster']
            dest_cluster_name = request.form['dest_cluster_name']
            rep_compression_mode = request.form['rep_compression_mode']

            if rep_compression_mode == 'enabled':
                rep_compression_algorithm = request.form['rep_compression_algorithm']
                replication_job.compression_algorithm = rep_compression_algorithm
            if rep_compression_mode == 'disabled':
                replication_job.compression_algorithm = ""

            pre_snap_script = request.form['pre_snap_script']
            post_snap_script = request.form['post_snap_script']
            post_job_complete = request.form['post_job_complete']

            remote_replication.disk_id = replication_job.destination_disk_id
            remote_replication.cluster_name = dest_cluster_name
            replication_job.job_name = job_name
            replication_job.schedule = schedule_object
            replication_job.node_name = backup_node
            replication_job.source_cluster_name = source_cluster_name
            replication_job.destination_cluster_name = dest_cluster_name
            replication_job.pre_snap_url = pre_snap_script
            replication_job.post_snap_url = post_snap_script
            replication_job.post_job_complete = post_job_complete

            # update src and dest disk meta.replication_info.
            manage_destination_cluster = ManageDestinationCluster()
            manage_replication.edit_replication_job(replication_job, old_node)
            session['success'] = "ui_admin_edit_job_success"
            return redirect(url_for('replication_controller.job_list'))

        except ReplicationException as e:
            logger.error(e)
            if e.id == ReplicationException.CONNECTION_REFUSED:
                session['err'] = "ui_admin_add_job_connction_refused_err"
                return redirect(url_for('replication_controller.add_job'))

            elif e.id == ReplicationException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_add_job_connction_timeout_err"
                return redirect(url_for('replication_controller.add_job'))

            elif e.id == ReplicationException.DUPLICATE_NAME:
                session['err'] = "ui_admin_add_job_duplicate_err"
                return redirect(url_for('replication_controller.add_job'))

            elif e.id == ReplicationException.PERMISSION_DENIED:
                session['err'] = "Permission Denied."
                return redirect(url_for('replication_controller.add_job'))

            elif e.id == ReplicationException.GENERAL_EXCEPTION:
                session['err'] = "core_consul_exception_cant_edit_rep_job"
                return redirect(url_for('replication_controller.add_job'))

        except Exception as e:
            logger.error(e)
            session['err'] = "ui_admin_edit_job_error"
            return redirect(url_for('replication_controller.view_job'))


@replication_controller.route('/replication/active_jobs_list', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def get_active_jobs_list():
    """
    DOCSTRING : this function gets ( all active replication jobs ) from Consul .
    Args : None
    Returns : List of all active replication jobs .
    """
    if request.method == 'GET' or request.method == 'POST':
        running_jobs = []
        try:
            manage_rep = ManageReplicationJobs()
            active_jobs = manage_rep.get_replication_active_jobs()
            if len(active_jobs) > 0:
                for job_id, job_info in active_jobs.iteritems():
                    running_jobs.append(job_info.__dict__)
                return json.dumps(running_jobs)
            else:
                return running_jobs

        except Exception as e:
            logger.error(e)
            return running_jobs


@replication_controller.route('/replication/cancel_active_job/<job_id>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def cancel_job(job_id):
    """
    DOCSTRING : this function is called to stop a certain active replication job from completing execution .
    Args : job_id (string)
    Returns : redirect to the page : 'admin/replication/job_list.html'
    """
    if request.method == 'POST':
        try:
            rep_handler = ReplicationHandler()
            result = rep_handler.force_cancel_active_job(job_id)
            if result:
                session['success'] = "ui_admin_success_deleting_active_job"
            else:
                session['err'] = "ui_admin_error_deleting_active_job"

        except Exception as e:
            logger.error(e)
            session['err'] = "ui_admin_error_deleting_active_job"

        return redirect(url_for('replication_controller.job_list'))


@replication_controller.route('/replication/Job_details/<job_id>', methods=['GET', 'POST'])
@requires_auth
@authorization('ReplicationJobs')
def job_details(job_id):
    """
    DOCSTRING : this function is used for modal information ...
    """
    if request.method == 'GET' or request.method == 'POST':
        try:
            replication_job = get_selected_Job_info(job_id)
            json_data = json.dumps(replication_job.__dict__, sort_keys=True)
            return json_data

        except Exception as e:
            session['err'] = "ui_admin_view_job_details_error"
            result = session['err']
            logger.error(e)
            return redirect(url_for('replication_controller.job_list'))

