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

from PetaSAN.core.common.CustomException import CephException, PoolException
from PetaSAN.core.cluster.configuration import *
from PetaSAN.backend.manage_crush import ManageCrush
from PetaSAN.backend.manage_ec_profiles import ManageEcProfiles
from PetaSAN.core.entity.models.ec_profile import ECProfile
from PetaSAN.core.entity.models.pool_info import PoolInfo
from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.backend.manage_pools import ManagePools
from PetaSAN.core.common.log import logger

from PetaSAN.core.ceph.api import CephAPI
#test
import datetime

pool_controller = Blueprint('pool_controller', __name__)

list_err = "err"
list_warning = "warning"
list_success = "success"


@pool_controller.route('/configuration/pools/', methods=['GET', 'POST'])
@pool_controller.route('/configuration/pools/<delete_job_id>/<pool_name>', methods=['GET', 'POST'])
@requires_auth
@authorization("PoolsList")
def get_pools(delete_job_id=-1, pool_name=""):
    """
    DOCSTRING : this function get ( all the pools + all the active pools ) then render to the page :
    'admin/pool/pools_list.html'.
    Args : None
    Returns : render to the template page : 'admin/pool/pools_list.html'
    """

    base_url = request.base_url
    global result

    if request.method == 'GET' or request.method == 'POST':
        try:
            manage_pool = ManagePools()
            pools_list = manage_pool.get_pools_info()
            active_pool_list = manage_pool.get_active_pools()
            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('admin/pool/pools_list.html', base_url=base_url, pools_list=pools_list,
                                       delete_job_id=delete_job_id, pool_name=pool_name,
                                       active_pool_list=active_pool_list, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('admin/pool/pools_list.html', base_url=base_url, pools_list=pools_list,
                                       delete_job_id=delete_job_id, pool_name=pool_name,
                                       active_pool_list=active_pool_list, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('admin/pool/pools_list.html', base_url=base_url, pools_list=pools_list,
                                       delete_job_id=delete_job_id, pool_name=pool_name,
                                       active_pool_list=active_pool_list, warning=result)

            else:
                return render_template('admin/pool/pools_list.html',
                                       delete_job_id=delete_job_id, pool_name=pool_name,
                                       base_url=base_url, active_pool_list=active_pool_list, pools_list=pools_list)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                result = session['err'] = "ui_admin_ceph_time_out"

            elif e.id == CephException.GENERAL_EXCEPTION:
                result = session['err'] = "ui_admin_ceph_general_exception"

            else:
                result = session['err'] = "ui_admin_ceph_general_exception"

            logger.error(e)
            return render_template('admin/pool/pools_list.html', delete_job_id=delete_job_id,
                                   base_url=base_url, err=result)

        except Exception as e:
            session['err'] = "ui_admin_view_pool_error"
            result = session['err']
            logger.error(e)
            return render_template('admin/pool/pools_list.html', err=result)


@pool_controller.route('/configuration/pools/remove/<pool_name>/<pool_type>', methods=['POST'])
@requires_auth
@authorization("PoolsList")
def remove_pool(pool_name, pool_type):
    """
    DOCSTRING : this function is called to delete a certain pool , then redirect to the page :
    'admin/pool/pools_list.html'.
    Args : pool_name (string)
    Returns : redirect to the page : 'admin/pool/pools_list.html'
    """

    if request.method == 'POST':
        try:

            manage_pool = ManagePools()
            pool_list = manage_pool.get_pools_info()
            pool_names = []
            for pool in pool_list:
                pool_names.append(pool.name)

            if pool_type == "erasure":
                delete_job_id = manage_pool.delete_pool(pool_name)


            elif pool_type == "replicated":
                ceph_api = CephAPI()
                pools = ceph_api.get_active_pools()
                if pool_name not in pools:
                    delete_job_id = manage_pool.delete_pool(pool_name)

                elif pool_name in pools:

                    meta_disk = ManageDisk().get_disks_meta_by_pool(pool_name)

                    if len(meta_disk) == 0:
                        delete_job_id = manage_pool.delete_pool(pool_name)

                    has_data_pool = 0
                    for disk in meta_disk:
                        if disk.data_pool is not None and disk.data_pool != "":
                            if disk.data_pool in pool_names:
                                has_data_pool += 1

                    if has_data_pool > 0:
                        session['err'] = "error_deleting_mata_pool"
                        return redirect(url_for('pool_controller.get_pools'))

                    else:
                        if len(meta_disk) > 0:
                            delete_job_id = manage_pool.delete_pool(pool_name)

            return redirect(url_for('pool_controller.get_pools', delete_job_id=delete_job_id, pool_name=pool_name))

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
                return redirect(url_for('pool_controller.get_pools'))

            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
                return redirect(url_for('pool_controller.get_pools'))

            session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return redirect(url_for('pool_controller.get_pools'))

        except Exception as e:
            session['err'] = "ui_admin_delete_pool_error"
            logger.error(e)
            return redirect(url_for('pool_controller.get_pools'))


@pool_controller.route('/pool/add', methods=['GET', 'POST'])
@requires_auth
@authorization("PoolsList")
def add_pool():
    """
    DOCSTRING : this function is called when opening the Add Pool form page.
    Args : None
    Returns : render to the template page : 'admin/pool/add_pool.html'
    """

    global result

    if request.method == 'GET' or request.method == 'POST':
        try:
            # getting the Rules List :
            manage_crush = ManageCrush()
            rule_list = manage_crush.get_rules()

            # getting the EC Profiles List :
            manage_ec_profiles = ManageEcProfiles()
            ec_profiles_list = manage_ec_profiles.get_ec_profiles()  # Dictionary of Objects

            # getting "storage_engine" from Cluster info :
            conf = configuration()
            ci = conf.get_cluster_info()
            storage_engine = ""
            storage_engine = ci.storage_engine

            if list_err in session:
                result = session["err"]
                session.pop("err")
                print(ec_profiles_list)
                return render_template('admin/pool/add_pool.html', rule_list=rule_list,
                                       ec_profiles_list=ec_profiles_list, storage_engine=storage_engine, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                print(ec_profiles_list)
                return render_template('admin/pool/add_pool.html', rule_list=rule_list,
                                       ec_profiles_list=ec_profiles_list, storage_engine=storage_engine, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                print(ec_profiles_list)
                return render_template('admin/pool/add_pool.html', rule_list=rule_list,
                                       ec_profiles_list=ec_profiles_list, storage_engine=storage_engine, warning=result)

            else:
                return render_template('admin/pool/add_pool.html', rule_list=rule_list,
                                       ec_profiles_list=ec_profiles_list, storage_engine=storage_engine)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return render_template('admin/pool/add_pool.html')

        except Exception as e:
            session['err'] = "ui_admin_view_pool_error"
            logger.error(e)
            return render_template('admin/pool/add_pool.html')


@pool_controller.route('/pool/save', methods=['POST'])
@requires_auth
@authorization("PoolsList")
def save_pool():
    """
    DOCSTRING : this function is called at saving a new pool , if saving operation is succeeded it renders to the
    template page : 'admin/pool/pools_list.html' with a success message , and if not it redirects
    to : 'admin/pool/add_pool.html' with an error message ...
    Args : None
    Returns : in success , it renders to : 'admin/pool/pools_list.html' with a success message
    in failure , it redirects to : 'admin/pool/add_pool.html'
    """

    if request.method == 'POST':
        try:
            # Get data from the form :
            name = (request.form['name'])
            type = (request.form['pool_type'])

            # If the pool was "Replicated" ...
            # --------------------------------
            if type == "replicated":
                pg_num = (request.form['rep_pg_num'])
                size = (request.form['rep_replica_size'])
                min_size = (request.form['rep_replica_min_size'])
                compression_mode = (request.form['rep_compression_mode'])

                if compression_mode == "enabled":
                    compression_mode = "force"
                    compression_algorithm = (request.form['rep_compression_algorithm'])
                else:
                    compression_mode = "none"
                    compression_algorithm = "none"

                rule_name = (request.form['rep_rule_name'])

            # If the pool was "Erasure" ...
            # --------------------------------
            elif type == "erasure":
                ec_profile = (request.form['ec_profile'])
                # splite to get only the profile name from the obtained value
                ec_profile = ec_profile.split("##")[0]
                print(ec_profile)
                pg_num = (request.form['ec_pg_num'])
                k = (request.form['ec_K'])
                k = int(k)
                m = (request.form['ec_M'])
                m = int(m)
                size = k + m
                min_size = (request.form['ec_min_size'])
                compression_mode = (request.form['ec_compression_mode'])

                if compression_mode == "enabled":
                    compression_mode = "force"
                    compression_algorithm = (request.form['ec_compression_algorithm'])
                else:
                    compression_mode = "none"
                    compression_algorithm = "none"

                rule_name = (request.form['ec_rule_name'])
                # splite to get only the profile name from the obtained value
                rule_name = rule_name.split("##")[0]

            # Creating an instance from Class : PoolInfo() :
            pool_info = PoolInfo()

            # Set the attributes of this instance :
            pool_info.name = name
            pool_info.type = type
            if type == "erasure":
                pool_info.ec_profile = ec_profile
            pool_info.pg_num = pg_num
            pool_info.size = size
            pool_info.min_size = min_size
            pool_info.compression_mode = compression_mode
            pool_info.compression_algorithm = compression_algorithm
            pool_info.rule_name = rule_name

            # Creating an instance from Class : ManagePools() :
            manage_pools = ManagePools()
            pool_list = manage_pools.get_pools_info()

            # Check on the duplication of pool name :
            if not unique_pool_name(pool_info.name, pool_list):
                session['err'] = "ui_admin_add_pool_err_duplicate"
                return redirect(url_for('pool_controller.add_pool'))

            # Saving new pool :
            manage_pools.add_pool(pool_info)
            session['success'] = "ui_admin_add_pool_success"
            return redirect(url_for('pool_controller.get_pools'))

        except PoolException as e:

            if e.id == PoolException.DUPLICATE_NAME:
                session['err'] = "ui_admin_add_pool_err_duplicate"
                return redirect(url_for('pool_controller.add_pool'))

            elif e.id == PoolException.PARAMETER_SET:
                session['err'] = "Pool added successfully but failed to set the following parameter(s) : " + e.message
                return redirect(url_for('pool_controller.add_pool'))

            elif e.id == PoolException.SIZE_TOO_LARGE:
                session['err'] = "ui_admin_pool_size_too_large_error"
                return redirect(url_for('pool_controller.add_pool'))

            elif e.id == PoolException.SIZE_TOO_SMALL:
                session['err'] = "ui_admin_pool_size_too_small_error"
                return redirect(url_for('pool_controller.add_pool'))

            elif e.id == PoolException.OSD_PGS_EXCEEDED:
                session['err'] = "ui_admin_pool_osd_pgs_exceeded_error"
                return redirect(url_for('pool_controller.add_pool'))

            session['err'] = "ui_admin_pool_general_error"
            logger.error(e)
            return redirect(url_for('pool_controller.add_pool'))

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
                return redirect(url_for('pool_controller.add_pool'))

            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
                return redirect(url_for('pool_controller.add_pool'))

            session['err'] = "ui_admin_ceph_general_exception"
            return redirect(url_for('pool_controller.add_pool'))

        except Exception as e:
            session['err'] = "ui_admin_add_pool_err"
            logger.error(e)
            return redirect(url_for('pool_controller.add_pool'))


@requires_auth
@authorization("PoolsList")
def unique_pool_name(pool_name, pools_list):
    """
    DOCSTRING : this function checks on the uniqueness of the pool name ...
    Args : pool_name (string) , pools_list
    Returns : The return value is True if the pool name is taken , False otherwise.
    """

    status = True

    for pool_object in pools_list:
        if pool_object.name == pool_name:
            status = False
    return status


@pool_controller.route('/pool/edit/<pool_name>', methods=['GET', 'POST'])
@requires_auth
@authorization("PoolsList")
def get_pool_info(pool_name):
    """
    DOCSTRING : this function is called when opening the Edit Pool form page.
    Args : pool_name (string)
    Returns : redirect to the page : 'admin/pool/edit_pool.html'
    """

    global result

    if request.method == 'GET' or request.method == 'POST':
        try:
            selected_pool_profile = ECProfile()
            manage_pools = ManagePools()
            pool_list = manage_pools.get_pools_info()
            for pool_info in pool_list:
                if pool_info.name == pool_name:
                    selected_pool = pool_info

            # If the pool was "Erasure" ... get the profile :
            # -----------------------------------------------
            if selected_pool.type == "erasure":
                # getting the EC Profiles List
                manage_ec_profiles = ManageEcProfiles()
                profiles_list = manage_ec_profiles.get_ec_profiles()  # Dictionary of Objects

                for profile_name, profile_obj in profiles_list.items():
                    if profile_name == selected_pool.ec_profile:
                        selected_pool_profile = profile_obj

            manage_crush = ManageCrush()
            rule_list = manage_crush.get_rules()

                        # getting "storage_engine" from Cluster info :
            conf = configuration()
            ci = conf.get_cluster_info()
            storage_engine = ""
            storage_engine = ci.storage_engine

            if list_err in session:
                result = session["err"]
                session.pop("err")
                return render_template('admin/pool/edit_pool.html', selected_pool=selected_pool, rule_list=rule_list,
                                       selected_pool_profile=selected_pool_profile, storage_engine=storage_engine, err=result)

            elif list_success in session:
                result = session["success"]
                session.pop("success")
                return render_template('admin/pool/edit_pool.html', selected_pool=selected_pool, rule_list=rule_list,
                                       selected_pool_profile=selected_pool_profile, storage_engine=storage_engine, success=result)

            elif list_warning in session:
                result = session["warning"]
                session.pop("warning")
                return render_template('admin/pool/edit_pool.html', selected_pool=selected_pool, rule_list=rule_list,
                                       selected_pool_profile=selected_pool_profile, storage_engine=storage_engine, warning=result)

            else:
                return render_template('admin/pool/edit_pool.html', selected_pool=selected_pool, rule_list=rule_list,
                                       selected_pool_profile=selected_pool_profile, storage_engine=storage_engine)

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                result = session['err'] = "ui_admin_ceph_time_out"
                return render_template('admin/pool/edit_pool.html', err=result)

            elif e.id == CephException.GENERAL_EXCEPTION:
                result = session['err'] = "ui_admin_ceph_general_exception"
                logger.error(e)
                return render_template('admin/pool/edit_pool.html', err=result)

            result = session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return render_template('admin/pool/edit_pool.html', err=result)

        except Exception as e:
            result = session['err'] = "ui_admin_view_get_pool_info_error"
            logger.error(e)
            return render_template('admin/pool/edit_pool.html', err=result)


@pool_controller.route('/pool/save_edit', methods=['POST'])
@requires_auth
@authorization("PoolsList")
def edit_pool():
    """
    DOCSTRING : this function is called at editing a specific pool , if editing operation is succeeded it renders to the
    template page : 'admin/pool/pools_list.html' with a success message , and if not it redirects
    to : 'admin/pool/edit_pool.html' with an error message ...
    Args : None
    Returns : in success , it renders to : 'admin/pool/pools_list.html' with a success message
    in failure , it redirects to : 'admin/pool/edit_pool.html'
    """

    if request.method == 'POST':

        try:
            # Get data from the form :
            name = (request.form['name'])
            type = (request.form['pool_type'])

            # If the pool was "Replicated" ...
            # --------------------------------
            if type == "replicated":
                pg_num = (request.form['rep_pg_num'])
                size = (request.form['rep_replica_size'])
                min_size = (request.form['rep_replica_min_size'])
                compression_mode = (request.form['rep_compression_mode'])

                if compression_mode == "enabled":
                    compression_mode = "force"
                    compression_algorithm = (request.form['rep_compression_algorithm'])
                else:
                    compression_mode = "none"
                    compression_algorithm = "none"

                rule_name = (request.form['rep_rule_name'])

            # If the pool was "Erasure" ...
            # --------------------------------
            elif type == "erasure":
                ec_profile = (request.form['ec_profile'])
                pg_num = (request.form['ec_pg_num'])
                k = (request.form['ec_K'])
                k = int(k)
                m = (request.form['ec_M'])
                m = int(m)
                size = k + m
                min_size = (request.form['ec_min_size'])
                compression_mode = (request.form['ec_compression_mode'])

                if compression_mode == "enabled":
                    compression_mode = "force"
                    compression_algorithm = (request.form['ec_compression_algorithm'])
                else:
                    compression_mode = "none"
                    compression_algorithm = "none"

                rule_name = (request.form['ec_rule_name'])
                # splite to get only the profile name from the obtained value
                rule_name = rule_name.split("##")[0]

            # Creating an instance from Class : PoolInfo() :
            selected_pool_info = PoolInfo()

            # Set the attributes of this instance :
            selected_pool_info.name = name
            selected_pool_info.type = type
            if type == "erasure":
                selected_pool_info.ec_profile = ec_profile
            selected_pool_info.pg_num = pg_num
            selected_pool_info.size = size
            selected_pool_info.min_size = min_size
            selected_pool_info.compression_mode = compression_mode
            selected_pool_info.compression_algorithm = compression_algorithm
            selected_pool_info.rule_name = rule_name

            # Creating an instance from Class : ManagePools() :
            manage_pools = ManagePools()

            # Updating pool :
            manage_pools.update_pool(selected_pool_info)
            session['success'] = "ui_admin_edit_pool_success"
            return redirect(url_for('pool_controller.get_pools'))

        except PoolException as e:

            if e.id == PoolException.DUPLICATE_NAME:
                session['err'] = "ui_admin_add_pool_err_duplicate"
                return redirect(url_for('pool_controller.get_pool_info', pool_name=selected_pool_info.name))

            elif e.id == PoolException.PARAMETER_SET:
                session['err'] = "Errors encountered while setting the following parameters : " + e.message
                return redirect(url_for('pool_controller.get_pool_info', pool_name=selected_pool_info.name))

            elif e.id == PoolException.SIZE_TOO_LARGE:
                session['err'] = "ui_admin_pool_size_too_large_error"
                return redirect(url_for('pool_controller.get_pool_info', pool_name=selected_pool_info.name))

            elif e.id == PoolException.SIZE_TOO_SMALL:
                session['err'] = "ui_admin_pool_size_too_small_error"
                return redirect(url_for('pool_controller.get_pool_info', pool_name=selected_pool_info.name))

            elif e.id == PoolException.OSD_PGS_EXCEEDED:
                session['err'] = "ui_admin_pool_osd_pgs_exceeded_error"
                return redirect(url_for('pool_controller.get_pool_info', pool_name=selected_pool_info.name))

            session['err'] = "ui_admin_pool_general_error"
            logger.error(e)
            return redirect(url_for('pool_controller.get_pool_info', pool_name=selected_pool_info.name))

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                session['err'] = "ui_admin_ceph_time_out"
                return redirect(url_for('pool_controller.get_pool_info', pool_name=selected_pool_info.name))

            elif e.id == CephException.GENERAL_EXCEPTION:
                session['err'] = "ui_admin_ceph_general_exception"
                return redirect(url_for('pool_controller.get_pool_info', pool_name=selected_pool_info.name))

            session['err'] = "ui_admin_ceph_general_exception"
            return redirect(url_for('pool_controller.get_pool_info', pool_name=selected_pool_info.name))

        except Exception as e:
            session['err'] = "ui_admin_edit_pool_err"
            logger.error(e)
            return redirect(url_for('pool_controller.get_pool_info', pool_name=selected_pool_info.name))


# get pool status as json data to use it in ajax call
@pool_controller.route('/configuration/pools/get_pool_status', methods=['GET', 'POST'])
@requires_auth
@authorization("PoolsList")
def get_pool_status():
    """
    DOCSTRING : this function is called by ajax request to get all the active pools
    Args : None
    Returns : json object of active pools list
    """


    if request.method == 'GET' or request.method == 'POST':
        # now_string_format = str(datetime.datetime.now()).split('.')[0]
        # now = datetime.datetime.strptime(now_string_format, "%Y-%m-%d %H:%M:%S")
        # print("inside get_pool_status()...")
        # print(now)
        # print("==================================================")
        global result
        manage_pool = ManagePools()
        # print("get active pools ....")
        active_pool_list = manage_pool.get_active_pools()
        # print("active pools= " , len(active_pool_list))
        # print("get pools info ....")
        pool_list = manage_pool.get_pools_info()
        # print("pools info=" , len(pool_list))
        pools = []
        for pool in pool_list:
            pool_dict = pool.__dict__
            pools.append(pool_dict)

        pools_dict = {"pools" : pools , "actives" : active_pool_list}
        # print("pools dict=" , pools_dict)

        json_data = json.dumps(pools_dict)
        return json_data


# get deleted pool Status as json data to use it in ajax call
@pool_controller.route('/configuration/pools/get_delete_status/<delete_id>', methods=['GET', 'POST'])
@requires_auth
@authorization("PoolsList")
def get_delete_status(delete_id):
    """
    DOCSTRING : this function is called by ajax request to get the status of the deleted pool ,
    whether its deletion is finished or not
    Args : delete_id
    Returns : json object of deleted pool status
    """

    manage_pool = ManagePools()
    delete_status = manage_pool.is_pool_deleting(delete_id)

    if request.method == 'GET' or request.method == 'POST':
        json_data = json.dumps(delete_status)
        return json_data


# ======================================================================================================================
# End of Manage Pool
# ======================================================================================================================


@pool_controller.route('/pool/<pool_name>')
@requires_auth
@authorization("PoolsList")
def get_selected_pool_info(pool_name):
    """
    DOCSTRING : this function is used for modal information ...
    """
    global result
    try:
        manage_pools = ManagePools()
        pool_list = manage_pools.get_pools_info()

        for pool_info in pool_list:
            if pool_info.name == pool_name:
                selected_pool = pool_info

        json_data = json.dumps(selected_pool.__dict__, sort_keys=True)
        return json_data

    except CephException as e:
        if e.id == CephException.CONNECTION_TIMEOUT:
            result = session['err'] = "ui_admin_ceph_time_out"
            return render_template('admin/pool/pools_list.html', err=result)

        elif e.id == CephException.GENERAL_EXCEPTION:
            result = session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return render_template('admin/pool/pools_list.html', err=result)

        result = session['err'] = "ui_admin_ceph_general_exception"
        logger.error(e)
        return render_template('admin/pool/pools_list.html', err=result)

    except Exception as e:
        result = session['err'] = "ui_admin_view_get_pool_info_error"
        logger.error(e)
        return render_template('admin/pool/pools_list.html', err=result)
