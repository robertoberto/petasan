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

from PetaSAN.core.common.CustomException import CephException
from PetaSAN.core.common.log import logger
from flask import Blueprint, render_template, request, redirect, url_for, session
import sys

from PetaSAN.core.security.basic_auth import requires_auth, authorization
from PetaSAN.backend.maintenance import ManageMaintenance
from PetaSAN.core.entity.maintenance import MaintenanceConfig
from PetaSAN.core.entity.models.maintenance import MaintenanceConfigForm
reload(sys)
sys.setdefaultencoding('utf-8')

maintenance_controller = Blueprint('maintenance_controller', __name__)


@maintenance_controller.route('/maintenance/config', methods=['GET'])
@requires_auth
@authorization("CLusterMaintenanceConfig")
def get_config():
    mesg_err = ""
    mesg_success = ""
    mesg_warning = ""
    if "err" in session:
        mesg_err = session["err"]
        session.pop("err")
    elif "success" in session:
        mesg_success = session["success"]
        session.pop("success")
    elif "warning" in session:
        mesg_warning = session["warning"]
        session.pop("warning")

    manage_maintenance = ManageMaintenance()
    maintenance_config = manage_maintenance.get_maintenance_config()

    maintenance_config_form = MaintenanceConfigForm()
    maintenance_config_form.fencing = int(maintenance_config.fencing)
    maintenance_config_form.osd_recover = int(maintenance_config.osd_recover)
    maintenance_config_form.osd_rebalance = int(maintenance_config.osd_rebalance)
    maintenance_config_form.osd_backfill = int(maintenance_config.osd_backfill)
    maintenance_config_form.osd_mark_down = int(maintenance_config.osd_down)
    maintenance_config_form.osd_mark_out = int(maintenance_config.osd_out)
    maintenance_config_form.osd_scrub = int(maintenance_config.osd_scrub)
    maintenance_config_form.osd_deep_scrub = int(maintenance_config.osd_deep_scrub)

    return render_template('/admin/maintenance/cluster_maintenance_config.html',
                           maintenance_config_form=maintenance_config_form, err=mesg_err,
                           success=mesg_success, warning=mesg_warning)


@maintenance_controller.route('/maintenance/config/save', methods=['POST'])
@requires_auth
@authorization("CLusterMaintenanceConfig")
def save_maintenance_setting():
    if request.method == 'POST':
        try:
            maintenance_config = MaintenanceConfig()
            maintenance_config.fencing = int(request.form['fencing'])
            maintenance_config.osd_recover = int(request.form['osd_recover'])
            maintenance_config.osd_rebalance = int(request.form['osd_rebalance'])
            maintenance_config.osd_backfill = int(request.form['osd_backfill'])
            maintenance_config.osd_down = int(request.form['osd_mark_down'])
            maintenance_config.osd_out= int(request.form['osd_mark_out'])
            maintenance_config.osd_scrub = int(request.form['osd_scrub'])
            maintenance_config.osd_deep_scrub = int(request.form['osd_deep_scrub'])

            ManageMaintenance().set_maintenance_config(maintenance_config)

            session['success'] = "ui_admin_save_maintenance_config_success"
        except Exception as e:
            session['err'] = "ui_admin_save_maintenance_config_error"
            logger.exception(e)
            return redirect(url_for('maintenance_controller.get_config'), 307)

        return redirect(url_for('maintenance_controller.get_config'))


@maintenance_controller.route('/maintenance/config/backfill_speed', methods=['GET'])
@requires_auth
@authorization("CLusterMaintenanceConfig")
def get_backfill_speed():
    """
    DOCSTRING : this function renders to the template page : 'admin/maintenance/set_backfill_speed.html'
    """
    mesg_err = ""
    mesg_success = ""
    mesg_warning = ""
    if "err" in session:
        mesg_err = session["err"]
        session.pop("err")
    elif "success" in session:
        mesg_success = session["success"]
        session.pop("success")
    elif "warning" in session:
        mesg_warning = session["warning"]
        session.pop("warning")

    return render_template('/admin/maintenance/set_backfill_speed.html', err=mesg_err,
                           success=mesg_success, warning=mesg_warning)


@maintenance_controller.route('/maintenance/config/set_backfill_speed', methods=['POST'])
@requires_auth
@authorization("CLusterMaintenanceConfig")
def save_backfill_speed():
    """
    DOCSTRING : this function renders to the template page : 'admin/maintenance/set_backfill_speed.html'
    """
    if request.method == 'POST':
        try:
            backfill_speed_no = int((request.form['backfillSpeeds']))

            manage_maintenance = ManageMaintenance()
            manage_maintenance.set_backfill_speed(backfill_speed_no)

            session['success'] = "ui_admin_set_backfill_speed_success"
            return redirect(url_for('maintenance_controller.get_backfill_speed'))

        except CephException as e:
            if e.id == CephException.CONNECTION_TIMEOUT:
                result = session['err'] = "ui_admin_ceph_time_out"
                return render_template('/admin/maintenance/set_backfill_speed.html', err=result)

            elif e.id == CephException.GENERAL_EXCEPTION:
                result = session['err'] = "ui_admin_ceph_general_exception"
                logger.error(e)
                return render_template('/admin/maintenance/set_backfill_speed.html', err=result)

            result = session['err'] = "ui_admin_ceph_general_exception"
            logger.error(e)
            return render_template('/admin/maintenance/set_backfill_speed.html', err=result)

        except Exception as e:
            result = session['err'] = "ui_admin_set_backfill_speed_error"
            logger.error(e)
            return render_template('/admin/maintenance/set_backfill_speed.html', err=result)
