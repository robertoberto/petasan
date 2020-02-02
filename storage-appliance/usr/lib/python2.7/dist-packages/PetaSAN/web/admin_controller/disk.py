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
from itertools import repeat

from PetaSAN.backend.mange_path_assignment import MangePathAssignment
from PetaSAN.core.ceph import ceph_disk as ceph_disk
from PetaSAN.core.entity.path_assignment import PathAssignmentInfo
from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.backend.manage_config import ManageConfig
from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.backend.manage_pools import ManagePools
from PetaSAN.core.entity.disk_info import DiskMeta
from PetaSAN.core.entity.models.disks import add_disk_form
from PetaSAN.core.common.enums import ManageDiskStatus, DisplayDiskStatus
from PetaSAN.core.common.enums import PathType
from PetaSAN.core.cluster.configuration import *
from PetaSAN.core.common.CustomException import CephException

disk_controller = Blueprint('disk_controller', __name__)

list_err = "err"
list_warning = "warning"
list_success = "success"


@disk_controller.route('/disk/add', methods=['POST', 'GET'])
@requires_auth
@authorization("AddDisk")
def add_disk():
    if request.method == 'GET' or request.method == 'POST':
        manage_config = ManageConfig()
        subnet1_info = manage_config.get_iscsi1_subnet()
        subnet2_info = manage_config.get_iscsi2_subnet()
        size_list_aval = [1, 2, 3, 4, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 250, 300, 400, 450, 500, 600,
                          700, 800, 900, 1024, 2048,
                          3072, 4096, 5120, 10240, 20480, 30720, 51200, 102400]
        active_pools = []
        replicated_pools = []
        erasure_pools = []
        result = ""
        failed_pools = 0
        try:
            manage_pool = ManagePools()
            active_pools = manage_pool.get_active_pools()
            all_pools = manage_pool.get_pools_info()
            for pool in all_pools:
                if pool.name in active_pools and pool.type == 'replicated':
                    replicated_pools.append(pool.name)
                elif pool.name in active_pools and pool.type == 'erasure':
                    erasure_pools.append(pool.name)
            if len(all_pools) > len(active_pools):
                failed_pools = len(all_pools) - len(active_pools)
        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                result = "Ceph connection timeout"
            elif e.id == CephException.GENERAL_EXCEPTION:
                result = "Ceph general exception"
            logger.error(e)
            form1 = add_disk_form()
            return render_template('admin/disk/add_disk.html', subnet1=subnet1_info, subnet2=subnet2_info,
                                   size_list=size_list_aval, err=result, form=form1, failed_pools=failed_pools,
                                   erasure_pools=sorted(erasure_pools), replicated_pools=sorted(replicated_pools),
                                   pools=sorted(active_pools))
        if list_err in session:
            result = session[list_err]
            session.pop(list_err)
            return render_template('admin/disk/add_disk.html', subnet1=subnet1_info, subnet2=subnet2_info,
                                   size_list=size_list_aval, err=result, form=request.form, failed_pools=failed_pools,
                                   erasure_pools=sorted(erasure_pools), replicated_pools=sorted(replicated_pools),
                                   pools=sorted(active_pools))
        elif list_warning in session:
            result = session[list_warning]
            session.pop(list_warning)
            return render_template('admin/disk/add_disk.html', subnet1=subnet1_info, subnet2=subnet2_info,
                                   size_list=size_list_aval, warning=result, form=request.form,
                                   failed_pools=failed_pools, erasure_pools=sorted(erasure_pools),
                                   replicated_pools=sorted(replicated_pools), pools=sorted(active_pools))
        elif list_success in session:
            result = session[list_success]
            session.pop(list_success)
            return render_template('admin/disk/add_disk.html', subnet1=subnet1_info, subnet2=subnet2_info,
                                   size_list=size_list_aval, success=result, form=request.form,
                                   failed_pools=failed_pools, erasure_pools=sorted(erasure_pools),
                                   replicated_pools=sorted(replicated_pools), pools=sorted(active_pools))
        else:
            form1 = add_disk_form()
            return render_template('admin/disk/add_disk.html', subnet1=subnet1_info, subnet2=subnet2_info,
                                   size_list=size_list_aval, form=form1, failed_pools=failed_pools,
                                   erasure_pools=sorted(erasure_pools), replicated_pools=sorted(replicated_pools),
                                   pools=sorted(active_pools))


@disk_controller.route('/disk/add/save', methods=['POST'])
@requires_auth
@authorization("AddDisk")
def save_disk():
    if request.method == 'POST':
        try:
            failed_pools = int(request.form['failed_pools'])
            activePaths = int(request.form['ActivePaths'])
            if activePaths >= 3:
                automatic_ip = "Yes"
            else:
                automatic_ip = request.form['orpUseFirstRange']
            if automatic_ip == "Yes" and failed_pools > 0:
                session['err'] = "ui_admin_add_disk_while_pool_inactive"
                return redirect(url_for('disk_controller.add_disk'), 307)
            disk = DiskMeta()
            disk.size = int(request.form['diskSize'])
            disk.disk_name = request.form['diskName']
            disk.pool = request.form['pool']
            if request.form['pool_type'] == "erasure":
                disk.data_pool = request.form['erasure_pool']
            else:
                disk.data_pool = ""

            if 'orpUseFirstRange' not in request.values:
                isAutomaticIp = "Yes"
            else:
                isAutomaticIp = request.form['orpUseFirstRange']

            activePathsCount = int(request.form['ActivePaths'])
            if activePathsCount >= 3:
                isAutomaticIp = "Yes"
            path_type = int(request.form['ISCSISubnet'])
            if path_type == 1:
                path_type = PathType.iscsi_subnet1
            elif path_type == 2:
                path_type = PathType.iscsi_subnet2
            elif path_type == 3:
                path_type = PathType.both
            manual_ips = []

            if isAutomaticIp != "Yes":
                manual_ips.append(request.form['path1'])
                isAutomaticIp = False
                if activePathsCount == 2:
                    manual_ips.append(request.form['path2'])
            else:
                isAutomaticIp = True

            disk.orpUseFirstRange = isAutomaticIp
            disk.ISCSISubnet = int(request.form['ISCSISubnet'])

            usedACL = request.form['orpACL']
            if usedACL == "Iqn":
                disk.acl = request.form['IqnVal']
            else:
                disk.acl = ""

            usedAutentication = request.form['orpAuth']
            if usedAutentication == "Yes":
                auth_auto = False
                disk.user = request.form['UserName']
                disk.password = request.form['Password']
            else:
                auth_auto = True

            enable_rep = request.form['replication']
            if enable_rep == "yes":
                disk.is_replication_target = True
            manage_config = ManageConfig()
            subnet1_info = manage_config.get_iscsi1_subnet()
            subnet2_info = manage_config.get_iscsi2_subnet()
            disk.subnet1 = subnet1_info.subnet_mask
            manageDisk = ManageDisk()
            status = manageDisk.add_disk(disk, manual_ips, path_type, activePathsCount, auth_auto, isAutomaticIp,
                                         disk.pool)
            if status == ManageDiskStatus.done:
                # session['success'] = "ui_admin_add_disk_success"
                return redirect(url_for('disk_controller.disk_list'))

            elif status == ManageDiskStatus.done_metaNo:
                session['success'] = "ui_admin_add_disk_created_with_no_metadata"
                return redirect(url_for('disk_controller.disk_list'))

            elif status == ManageDiskStatus.error:
                session['err'] = "ui_admin_add_disk_error"
                return redirect(url_for('disk_controller.add_disk'), 307)

            elif status == ManageDiskStatus.disk_created_cant_start:
                session['warning'] = "ui_admin_add_disk_created_not_start"
                return redirect(url_for('disk_controller.disk_list'))

            elif status == ManageDiskStatus.data_missing:
                session['err'] = "ui_admin_manage_disk_data_missing"
                return redirect(url_for('disk_controller.add_disk'), 307)

            elif status == ManageDiskStatus.disk_meta_cant_read:
                session['warning'] = "ui_admin_add_disk_error_created_not_read_metadata"
                return redirect(url_for('disk_controller.disk_list'))

            elif status == ManageDiskStatus.disk_exists:
                session['err'] = "ui_admin_manage_disk_exist"
                return redirect(url_for('disk_controller.add_disk'), 307)

            elif status == ManageDiskStatus.disk_name_exists:
                session['err'] = "ui_admin_manage_disk_name_exist"
                return redirect(url_for('disk_controller.add_disk'), 307)

            elif status == ManageDiskStatus.ip_out_of_range:
                session['err'] = "ui_admin_manage_disk_no_auto_ip"
                return redirect(url_for('disk_controller.add_disk'), 307)

            elif status == ManageDiskStatus.wrong_subnet:
                session['err'] = "ui_admin_manage_disk_wrong_subnet"
                return redirect(url_for('disk_controller.add_disk'), 307)

            elif status == ManageDiskStatus.wrong_data:
                session['err'] = "ui_admin_manage_disk_subnet_count"
                return redirect(url_for('disk_controller.add_disk'), 307)

            elif status == ManageDiskStatus.used_already:
                session['err'] = "ui_admin_manage_disk_used_already"
                return redirect(url_for('disk_controller.add_disk'), 307)

            elif status == ManageDiskStatus.disk_get__list_error:
                session['err'] = "ui_admin_manage_disk_disk_get_list_error"
                return redirect(url_for('disk_controller.add_disk'), 307)

        except Exception as e:
            session['err'] = "ui_admin_add_disk_error"
            logger.error(e)
            return redirect(url_for('disk_controller.add_disk'), 307)


# view list of disks
@disk_controller.route('/disk/list', methods=['GET', 'POST'])
@disk_controller.route('/disk/list/<delete_job_id>/<disk_id>/<pool>', methods=['GET', 'POST'])
@requires_auth
@authorization("DiskList")
def disk_list(delete_job_id=-1, disk_id="", pool=""):
    mesg_err = ""
    mesg_success = ""
    mesg_warning = ""
    available_disk_list = []
    disk_status = None
    active_paths = None
    base_url = request.base_url
    disk_id = disk_id
    cluster_fsid = ""
    try:
        manage_disk = ManageDisk()
        available_disk_list = manage_disk.get_disks_meta()
        cluster_fsid = ceph_disk.get_fsid(configuration().get_cluster_name())
        disk_status = DisplayDiskStatus
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
        mesg_err = "error in loading page"

    return render_template('admin/disk/list.html', diskList=available_disk_list, diskStatus=disk_status,cluster_fsid = cluster_fsid,
                           err=mesg_err, base_url=base_url, disk_id=disk_id, delete_job_id=delete_job_id,
                           pool=pool, success=mesg_success, warning=mesg_warning)


@disk_controller.route('/disk/list/stop/<disk_id>', methods=['GET', 'POST'])
@requires_auth
@authorization("DiskList")
def stop_disk(disk_id):
    if request.method == 'GET' or request.method == 'POST':

        manage_disk = ManageDisk()
        status = manage_disk.stop(disk_id)
        if (status != Status.done):
            # session['success'] = "ui_admin_stop_disk_success"
            # else:
            session['err'] = "ui_admin_stop_disk_error"
        return redirect(url_for('disk_controller.disk_list'))


@disk_controller.route('/disk/list/start/<disk_id>/<pool>', methods=['GET', 'POST'])
@requires_auth
@authorization("DiskList")
def start_disk(disk_id, pool):
    if request.method == 'GET' or request.method == 'POST':
        manage_disk = ManageDisk()
        status = manage_disk.start(disk_id, pool)
        if (status != Status.done):
            # session['success'] = "ui_admin_start_disk_success"
            # else:
            session['err'] = "ui_admin_start_disk_error"

        return redirect(url_for('disk_controller.disk_list'))


@disk_controller.route('/disk/list/edit/<disk_id>/<pool>', methods=['GET', 'POST'])
@requires_auth
@authorization("DiskList")
def edit_disk(disk_id, pool):
    if request.method == 'GET' or request.method == 'POST':
        size_list_aval = [1, 2, 3, 4, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 250, 300, 400, 450, 500, 600,
                          700, 800, 900, 1024, 2048,
                          3072, 4096, 5120, 10240, 20480, 30720, 51200, 102400]

        result = ""
        if list_err in session:

            result = session[list_err]
            session.pop(list_err)
            manage_disk = ManageDisk()
            disk = manage_disk.get_disk(disk_id, pool)
            return render_template('admin/disk/edit_disk.html', disk=disk, size_list=size_list_aval, err=result)

        elif list_warning in session:
            result = session[list_warning]
            session.pop(list_warning)
            manage_disk = ManageDisk()
            disk = manage_disk.get_disk(disk_id, pool)
            return render_template('admin/disk/edit_disk.html', disk=disk, size_list=size_list_aval, warning=result)

        elif list_success in session:
            result = session[list_success]
            session.pop(list_success)
            manage_disk = ManageDisk()
            disk = manage_disk.get_disk(disk_id, pool)
            return render_template('admin/disk/edit_disk.html', disk=disk, size_list=size_list_aval, success=result)

        else:
            manage_disk = ManageDisk()
            disk = manage_disk.get_disk(disk_id, pool)
            paths = disk.get_paths()
            config = configuration()
            iscsi_1_eth_name = config.get_cluster_info().iscsi_1_eth_name
            iscsi_2_eth_name = config.get_cluster_info().iscsi_2_eth_name
            paths_iscsi_1 = []
            paths_iscsi_2 = []
            for path in paths:
                if path.eth == iscsi_1_eth_name:
                    paths_iscsi_1.append(path.ip)
                elif path.eth == iscsi_2_eth_name:
                    paths_iscsi_2.append(path.ip)
            return render_template('admin/disk/edit_disk.html', disk=disk,
                                   paths_iscsi_1=paths_iscsi_1, paths_iscsi_2=paths_iscsi_2, size_list=size_list_aval)


@disk_controller.route('/disk/list/edit/update/<disk_id>/<pool>', methods=['POST'])
@requires_auth
@authorization("DiskList")
def update_disk(disk_id, pool):
    if request.method == 'POST':
        try:
            disk = DiskMeta()
            disk.id = disk_id
            disk.disk_name = request.form['diskName']
            disk.size = int(request.form['diskSize'])
            auth_auto = True
            acl = request.form['orpACL']
            if acl == "Iqn":
                disk.acl = request.form['IqnVal']
            # if 'clientACL' in request.form:
            #     usedACL = request.form['clientACL']
            #     if usedACL == "Yes":
            #         disk.acl = request.form['IqnVal']
            #     else:
            #         disk.acl = ""
            if 'orpAuth' in request.form:
                used_autentication = request.form['orpAuth']
                if used_autentication == "Yes":
                    auth_auto = False
                    disk.user = request.form['UserName']
                    disk.password = request.form['Password']

            disk.data_pool = request.form['data_pool']

            enable_rep = request.form['replication']
            if enable_rep == "yes":
                disk.is_replication_target = True
            manage_disk = ManageDisk()
            status = manage_disk.edit_disk(disk, auth_auto, pool)
            if status == ManageDiskStatus.done:
                session['success'] = "ui_admin_edit_disk_success"
                return redirect(url_for('disk_controller.disk_list'))

            elif status == ManageDiskStatus.error:
                session['err'] = "ui_admin_edit_disk_error"
                return redirect(url_for('disk_controller.edit_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.data_missing:
                session['err'] = "ui_admin_manage_disk_data_missing"
                return redirect(url_for('disk_controller.edit_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.disk_exists:
                session['err'] = "ui_admin_manage_disk_exist"
                return redirect(url_for('disk_controller.edit_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.disk_name_exists:
                session['err'] = "ui_admin_manage_disk_name_exist"
                return redirect(url_for('disk_controller.edit_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.disk_get__list_error:
                session['err'] = "ui_admin_manage_disk_disk_get_list_error"
                return redirect(url_for('disk_controller.edit_disk', disk_id=disk_id, pool=pool), 307)


        except Exception as e:
            session['err'] = "ui_admin_edit_disk_error"
            logger.error(e)
            return redirect(url_for('disk_controller.edit_disk', disk_id=disk_id, pool=pool), 307)


@disk_controller.route('/disk/list/detach/<disk_id>/<pool>', methods=['GET', 'POST'])
@requires_auth
@authorization("DiskList")
def detach_disk(disk_id, pool):
    if request.method == 'GET' or request.method == 'POST':

        manage_disk = ManageDisk()
        status = manage_disk.detach_disk(disk_id, pool)
        if (status != Status.done):
            # session['success'] = "ui_admin_detach_disk_success"
            # else:
            session['err'] = "ui_admin_detach_disk_error"

        return redirect(url_for('disk_controller.disk_list'))


@disk_controller.route('/disk/list/remove/<disk_id>/<pool>', methods=['GET', 'POST'])
@requires_auth
@authorization("DiskList")
def remove_disk(disk_id, pool):
    if request.method == 'GET' or request.method == 'POST':
        manage_disk = ManageDisk()
        delete_job_id = manage_disk.delete_disk(disk_id, pool)
        print ()
        return redirect(url_for('disk_controller.disk_list', delete_job_id=delete_job_id, disk_id=disk_id, pool=pool))

        # status = manage_disk.delete_disk(disk_id , pool)
        # if (status == Status.done):
        #     session['success'] = "ui_admin_delete_disk_success"
        # else:
        #     session['err'] = "ui_admin_delete_disk_remove"
        #
        # return redirect(url_for('disk_controller.disk_list'))


# get deleted disk Status as json data to use it in ajax call
@disk_controller.route('/disk/list/get_delete_status/<delete_id>', methods=['GET', 'POST'])
@requires_auth
@authorization("DiskList")
def get_delete_status(delete_id):
    """
    DOCSTRING : this function is called by ajax request to get the status of the deleted disk ,
    whether its deletion is finished or not
    Args : delete_id
    Returns : json object of deleted disk status
    """

    manage_disk = ManageDisk()
    delete_status = manage_disk.is_disk_deleting(delete_id)

    if request.method == 'GET' or request.method == 'POST':
        json_data = json.dumps(delete_status)
        return json_data


@disk_controller.route('/disk/list/attach/<disk_id>/<pool>', methods=['GET', 'POST'])
@requires_auth
@authorization("DiskList")
def attach_disk(disk_id, pool):
    if request.method == 'GET' or request.method == 'POST':
        failed_pools = 0
        manage_pool = ManagePools()
        active_pools = manage_pool.get_active_pools()
        all_pools = manage_pool.get_pools_info()
        if len(all_pools) > len(active_pools):
            failed_pools = len(all_pools) - len(active_pools)

        manage_config = ManageConfig()
        subnet1_info = manage_config.get_iscsi1_subnet()
        subnet2_info = manage_config.get_iscsi2_subnet()
        size_list_aval = [1, 2, 3, 4, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 250, 300, 400, 450, 500, 600,
                          700, 800, 900, 1024, 2048,
                          3072, 4096, 5120, 10240, 20480, 30720, 51200, 102400]

        result = ""
        if list_err in session:
            result = session[list_err]
            session.pop(list_err)
            manage_disk = ManageDisk()
            disk = manage_disk.get_disk(disk_id, pool)
            form1 = add_disk_form()
            form1.id = disk.id
            form1.diskSize = disk.size
            form1.pool = pool
            form1.data_pool = disk.data_pool
            form1.diskName = disk.disk_name
            form1.is_replication_target = disk.is_replication_target
            return render_template('admin/disk/attach_disk.html', subnet1=subnet1_info, subnet2=subnet2_info,
                                   form=form1, failed_pools=failed_pools,
                                   size_list=size_list_aval, err=result)

        elif list_warning in session:
            result = session[list_warning]
            session.pop(list_warning)
            manage_disk = ManageDisk()
            disk = manage_disk.get_disk(disk_id, pool)
            form1 = add_disk_form()
            form1.id = disk.id
            form1.diskSize = disk.size
            form1.pool = pool
            form1.data_pool = disk.data_pool
            form1.diskName = disk.disk_name
            form1.is_replication_target = disk.is_replication_target
            return render_template('admin/disk/attach_disk.html', subnet1=subnet1_info, subnet2=subnet2_info,
                                   form=form1, failed_pools=failed_pools,
                                   size_list=size_list_aval, warning=result)

        elif list_success in session:
            result = session[list_success]
            session.pop(list_success)
            manage_disk = ManageDisk()
            disk = manage_disk.get_disk(disk_id, pool)
            form1 = add_disk_form()
            form1.id = disk.id
            form1.diskSize = disk.size
            form1.pool = pool
            form1.data_pool = disk.data_pool
            form1.diskName = disk.disk_name
            form1.is_replication_target = disk.is_replication_target
            return render_template('admin/disk/attach_disk.html', subnet1=subnet1_info, subnet2=subnet2_info,
                                   form=form1, failed_pools=failed_pools,
                                   size_list=size_list_aval, success=result)

        else:
            is_not_petasan_warning = ''
            manage_disk = ManageDisk()
            disk = manage_disk.get_disk(disk_id, pool)
            form1 = add_disk_form()
            if disk.is_petasan_image is not None and disk.is_petasan_image == False:
                form1.diskName = disk.id
                is_not_petasan_warning = "ui_admin_attach_disk_warning_disk_is_not_petasan"
            form1.id = disk.id
            form1.diskSize = disk.size
            form1.pool = pool
            form1.data_pool = disk.data_pool
            form1.diskName = disk.disk_name
            form1.is_replication_target = disk.is_replication_target
            if is_not_petasan_warning != '':
                result = is_not_petasan_warning
            return render_template('admin/disk/attach_disk.html', subnet1=subnet1_info, subnet2=subnet2_info,
                                   form=form1, failed_pools=failed_pools,
                                   size_list=size_list_aval, warning=result)


@disk_controller.route('/disk/list/attach/save/<disk_id>/<pool>', methods=['POST'])
@requires_auth
@authorization("DiskList")
def save_attach_disk(disk_id, pool):
    if request.method == 'POST':
        try:
            failed_pools = int(request.form['failed_pools'])
            activePaths = int(request.form['ActivePaths'])
            if activePaths >= 3:
                automatic_ip = "Yes"
            else:
                automatic_ip = request.form['orpUseFirstRange']
            if automatic_ip == "Yes" and failed_pools > 0:
                session['err'] = "ui_admin_add_disk_while_pool_inactive"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)
            disk = DiskMeta()
            disk.id = disk_id
            disk.size = int(request.form['diskSize'])
            disk.disk_name = request.form['diskName']
            if 'orpUseFirstRange' not in request.values:
                isAutomaticIp = "Yes"
            else:
                isAutomaticIp = request.form['orpUseFirstRange']

            activePathsCount = int(request.form['ActivePaths'])
            if activePathsCount >= 3:
                isAutomaticIp = "Yes"
            path_type = int(request.form['ISCSISubnet'])
            if path_type == 1:
                path_type = PathType.iscsi_subnet1
            elif path_type == 2:
                path_type = PathType.iscsi_subnet2
            elif path_type == 3:
                path_type = PathType.both
            manual_ips = []
            enable_rep = request.form['replication']
            if enable_rep == "yes":
                disk.is_replication_target = True

            if isAutomaticIp != "Yes":
                manual_ips.append(request.form['path1'])
                isAutomaticIp = False
                if activePathsCount == 2:
                    manual_ips.append(request.form['path2'])
            else:
                isAutomaticIp = True

            disk.orpUseFirstRange = isAutomaticIp
            disk.ISCSISubnet = int(request.form['ISCSISubnet'])

            usedACL = request.form['orpACL']
            if usedACL == "Iqn":
                disk.acl = request.form['IqnVal']
            else:
                disk.acl = ""

            usedAutentication = request.form['orpAuth']
            if usedAutentication == "Yes":
                auth_auto = False
                disk.user = request.form['UserName']
                disk.password = request.form['Password']
            else:
                auth_auto = True

            disk.data_pool = request.form['data_pool']

            manage_config = ManageConfig()
            subnet1_info = manage_config.get_iscsi1_subnet()
            subnet2_info = manage_config.get_iscsi2_subnet()
            disk.subnet1 = subnet1_info.subnet_mask
            # call method to save object
            manageDisk = ManageDisk()
            status = manageDisk.attach_disk(disk, manual_ips, path_type, activePathsCount, auth_auto, isAutomaticIp,
                                            pool)
            if status == ManageDiskStatus.done:
                # session['success'] = "ui_admin_attach_disk_success"
                return redirect(url_for('disk_controller.disk_list'))

            elif status == ManageDiskStatus.done_metaNo:
                session['success'] = "ui_admin_attach_disk_attached_with_no_metadata"
                return redirect(url_for('disk_controller.disk_list'))

            elif status == ManageDiskStatus.error:
                session['err'] = "ui_admin_attach_disk_error"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.disk_created_cant_start:
                session['warning'] = "ui_admin_attach_disk_attached_not_start"
                return redirect(url_for('disk_controller.disk_list'))

            elif status == ManageDiskStatus.data_missing:
                session['err'] = "ui_admin_manage_disk_data_missing"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.disk_meta_cant_read:
                session['warning'] = "ui_admin_attach_disk_error_attached_not_read_metadata"
                return redirect(url_for('disk_controller.disk_list'))

            elif status == ManageDiskStatus.disk_exists:
                session['err'] = "ui_admin_manage_disk_exist"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.disk_name_exists:
                session['err'] = "ui_admin_manage_disk_name_exist"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.ip_out_of_range:
                session['err'] = "ui_admin_manage_disk_no_auto_ip"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.wrong_subnet:
                session['err'] = "ui_admin_manage_disk_wrong_subnet"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.wrong_data:
                session['err'] = "ui_admin_manage_disk_wrong_data"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.used_already:
                session['err'] = "ui_admin_manage_disk_used_already"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.disk_get__list_error:
                session['err'] = "ui_admin_manage_disk_disk_get_list_error"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)

            elif status == ManageDiskStatus.is_busy:
                session['err'] = "ui_admin_attach_disk_is_busy"
                return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)

        except Exception as e:
            session['err'] = "ui_admin_attach_disk_error"
            logger.error(e)
            return redirect(url_for('disk_controller.attach_disk', disk_id=disk_id, pool=pool), 307)


# get disk status as json data to use it in ajax call
@disk_controller.route('/disk/disk_list', methods=['GET'])
@requires_auth
@authorization("DiskList")
def get_disk_list():
    if request.method == 'GET':
        data = {}
        manage_disk = ManageDisk()
        available_disk_list = manage_disk.get_disks_meta()
        for index in range(len(available_disk_list)):
            data[available_disk_list[index].id] = available_disk_list[index].status

        # d = array(data)
        json_data = json.dumps(data)
        return json_data


@disk_controller.route('/disk/disk_paths/<disk_id>/<pool>', methods=['GET'])
@requires_auth
@authorization("DiskList")
def get_disk_paths(disk_id, pool):
    if request.method == 'GET':
        date = {}
        date_value = []
        manage_disk = ManageDisk()
        disk_paths = manage_disk.get_disk_paths(disk_id, pool)
        for index in range(len(disk_paths)):
            # add interface name
            interface_name = disk_paths[index].eth
            if disk_paths[index].vlan_id:
                interface_name = disk_paths[index].eth + "." + disk_paths[index].vlan_id
            date_value = [disk_paths[index].locked_by, interface_name]
            date[disk_paths[index].ip] = date_value
            json_data = json.dumps(date)
        return json_data


# @disk_controller.route('/disk/replication_status/<disk_id>/<pool>', methods=['GET'])
# @requires_auth
# @authorization("DiskList")
# def get_disk_replication_status(disk_id, pool):
#     if request.method == 'GET':
#         manage_disk = ManageDisk()
#         replication_status = False
#         replication_info = manage_disk.get_disk(disk_id, pool).replication_info
#         replication_target = manage_disk.get_disk(disk_id, pool).is_replication_target
#         source_fsid = ceph_disk.get_fsid(configuration().get_cluster_name())
#         if replication_info and replication_info["dest_cluster_fsid"]:
#             print(replication_info)
#             print(source_fsid)
#             replication_status = True
#         json_data = json.dumps(replication_status)
#         return json_data


@disk_controller.route('/disk/path_assignment/list', methods=['GET'])
@requires_auth
@authorization("PathAssignment")
def paths_list():
    mesg_err = ""
    mesg_success = ""
    try:
        if "err" in session:
            mesg_err = session["err"]
            session.pop("err")
        elif "success" in session:
            mesg_success = session["success"]
            session.pop("success")
        return render_template('/admin/disk/path_assignment_list.html', err=mesg_err, success=mesg_success)
    except Exception as e:
        logger.error(e)
        return render_template('/admin/disk/path_assignment_list.html', err=mesg_err)


@disk_controller.route('/disk/path_assignment', methods=['GET'])
@requires_auth
@authorization("PathAssignment")
def paths_assign():
    return render_template('/admin/disk/reassign_path.html')


@disk_controller.route('/disk/path_assignment/get_assignments_status', methods=['GET'])
@requires_auth
@authorization("PathAssignment")
def get_assignments_status():
    """
    DOCSTRING : this function is called to delete a certain pool , then redirect to the page :
    'admin/disk/path_assignment_list.html'.
    Args : none
    Returns : redirect to the page : list of all disks status
    """
    if request.method == 'GET':
        try:
            manage_paths = MangePathAssignment()
            logger.info("get object from MangePathAssignment.")
            show_list = manage_paths.get_assignments_stats()
            logger.info("call get assignments stats function.")
            return show_list.write_json()


        except Exception as e:
            logger.error(e)
            return -1


@disk_controller.route('/disk/path_assignment/search_by_name/<disk_name>', methods=['GET'])
@requires_auth
@authorization("PathAssignment")
def search_by_name(disk_name):
    if request.method == 'GET':
        try:
            manage_paths = MangePathAssignment()
            logger.info("get object from MangePathAssignment.")
            show_list = manage_paths.search_by_disk_name(disk_name)
            logger.info("call search by name function.")
            return show_list.write_json()

        except Exception as e:
            logger.error(e)
            return -1


@disk_controller.route('/disk/path_assignment/search_by_ip/<ip>', methods=['GET'])
@requires_auth
@authorization("PathAssignment")
def search_by_ip(ip):
    if request.method == 'GET':
        try:
            manage_paths = MangePathAssignment()
            logger.info("get object from MangePathAssignment.")
            show_list = manage_paths.search_by_ip(ip)
            logger.info("call search by ip function.")
            return show_list.write_json()

        except Exception as e:
            logger.error(e)
            return -1


@disk_controller.route('/disk/path_assignment/assign_paths/auto/<type>', methods=['POST'])
@requires_auth
@authorization("PathAssignment")
def auto_assign_paths(type):
    if request.method == 'POST':
        try:
            manage_path_assignment = MangePathAssignment()
            logger.info("get object from MangePathAssignment.")
            manage_path_assignment.auto(int(type))
            logger.info("call auto function.")
            # session['success'] = "ui_admin_disks_paths_assignment_list_success"
            logger.info("set success message and will redirect to paths list.")
            return redirect(url_for('disk_controller.paths_list'))

        except Exception as e:
            # session['err'] = "ui_admin_disks_paths_assignment_list_fail"
            logger.error(e)


@disk_controller.route('/disk/path_assignment/assign_paths/manual', methods=['POST'])
@requires_auth
@authorization("PathAssignment")
def manual_assign_paths():
    if request.method == 'POST':
        try:
            selected_paths = request.form.getlist('option_path[]')
            selected_paths_lst = [str(x) for x in selected_paths]
            paths_assign_info_lst = []
            logger.info("User starts manual assignments.")
            for path in selected_paths_lst:
                selected_paths_assign_info = path.split('##')

                paths_assign_info = PathAssignmentInfo()
                paths_assign_info.node = selected_paths_assign_info[0]
                paths_assign_info.disk_name = selected_paths_assign_info[1]
                paths_assign_info.ip = selected_paths_assign_info[2]
                paths_assign_info.disk_id = selected_paths_assign_info[3]

                paths_assign_info_lst.append(paths_assign_info)
                logger.info("User selected path {} {} {}.".format(paths_assign_info.disk_id,
                                                                  paths_assign_info.disk_name, paths_assign_info.node))

            assign_to = request.form.get('assign_to')
            manage_path_assignment = MangePathAssignment()
            if assign_to == "auto":
                logger.info("User selected auto option in manual assignment.")
                manage_path_assignment.manual(paths_assign_info_lst)
                logger.info("System started auto assignments.")
                # pass
            else:
                logger.info("User selected manual option in assignment.")
                manage_path_assignment.manual(paths_assign_info_lst, assign_to)
                logger.info("System started manual assignments.")

            session['success'] = "ui_admin_disks_paths_assignment_list_success"
            return redirect(url_for('disk_controller.paths_list'))

        except Exception as e:
            session['err'] = "ui_admin_disks_paths_assignment_list_fail"
            logger.error(e)


@disk_controller.route('/disk/list/<disk_id>/<pool>', methods=['GET', 'POST'])
@requires_auth
@authorization("DiskList")
def get_disk_info_by_id_pool(disk_id, pool):
    if request.method == 'GET' or request.method == 'POST':
        try:
            manage_disk = ManageDisk()
            disk = manage_disk.get_disk(disk_id, pool)
            paths = disk.get_paths()
            config = configuration()
            iscsi_1_eth_name = config.get_cluster_info().iscsi_1_eth_name
            iscsi_2_eth_name = config.get_cluster_info().iscsi_2_eth_name
            paths_iscsi_1 = []
            paths_iscsi_2 = []
            for path in paths:
                if path.eth == iscsi_1_eth_name:
                    paths_iscsi_1.append(path.ip)
                elif path.eth == iscsi_2_eth_name:
                    paths_iscsi_2.append(path.ip)
            disk = disk.__dict__
            disk.update({"paths_iscsi_1": paths_iscsi_1, "paths_iscsi_2": paths_iscsi_2})
            return json.dumps(disk)

        except Exception as e:
            logger.error(e)
            return -1
