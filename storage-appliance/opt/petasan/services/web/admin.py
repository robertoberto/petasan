#!/usr/bin/python
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

from datetime import timedelta
from flask import Flask, session
import resource

from PetaSAN.web.admin_controller.main import main_controller
from PetaSAN.web.admin_controller.disk import disk_controller
from PetaSAN.web.admin_controller.user import user_controller
from PetaSAN.web.admin_controller.node import node_controller
from PetaSAN.web.admin_controller.benchmark import benchmark_controller
from PetaSAN.web.admin_controller.maintenance import maintenance_controller
from PetaSAN.web.admin_controller.configuration import configuration_controller
from PetaSAN.core.cluster.network import Network
from PetaSAN.core.security.api import RoleAPI
from PetaSAN.core.security.session import ConsulSessionInterface
from PetaSAN.core.common.messages import *
from PetaSAN.web.admin_controller.crush import crush_controller
from PetaSAN.web.admin_controller.pool import pool_controller
from PetaSAN.web.admin_controller.ec_profile import ec_profile_controller
from PetaSAN.web.admin_controller.backup import backup_controller
from PetaSAN.web.admin_controller.replication import replication_controller
from PetaSAN.web.admin_controller.schedule import schedule_controller
from PetaSAN.web.admin_controller.replication_users import replication_users_controller
from PetaSAN.web.admin_controller.destination_cluster import destination_cluster_controller


app = Flask(__name__)
app.register_blueprint(main_controller)
app.register_blueprint(user_controller)
app.register_blueprint(disk_controller)
app.register_blueprint(configuration_controller)
app.register_blueprint(node_controller)
app.register_blueprint(benchmark_controller)
app.register_blueprint(maintenance_controller)
app.register_blueprint(crush_controller)
app.register_blueprint(pool_controller)
app.register_blueprint(ec_profile_controller)
# backup
app.register_blueprint(backup_controller)
# replication
app.register_blueprint(replication_controller)
app.register_blueprint(schedule_controller)
app.register_blueprint(replication_users_controller)
app.register_blueprint(destination_cluster_controller)

app.secret_key="petasan"
app.session_interface = ConsulSessionInterface()

def display_url(page_url):
    r = RoleAPI()

    return r.is_url_allowed(page_url,session['role_id'])

def display_url_by_page(page_name):
    r = RoleAPI()

    return r.is_page_allowed_by_name(page_name,session['role_id'])

def display_parent(parent_name):
      r = RoleAPI()

      return r.is_allowed_by_parent_name(parent_name,session['role_id'])





app.jinja_env.globals.update(display_url=display_url)
app.jinja_env.globals.update(display_url_by_page=display_url_by_page)
app.jinja_env.globals.update(display_parent=display_parent)
app.jinja_env.globals.update(gettext=gettext)
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)

if __name__ == '__main__':

    #soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (10240, 10240))

    #app.debug = True
    app.run(Network().get_node_management_ip(),port=5000,threaded=True)




