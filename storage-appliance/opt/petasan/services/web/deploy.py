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
from flask_session import Session

from PetaSAN.core.cluster.network import Network

# from PetaSAN.Web.DeployController.wizerd import wizerd_controller
from PetaSAN.web.deploy_controller.wizard import wizard_controller
from PetaSAN.core.common.messages import *

app = Flask(__name__)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

# app.register_blueprint(wizerd_controller)
app.register_blueprint(wizard_controller)

# app.session_interface = ConsulSessionInterface()
app.secret_key = "petasan"

app.jinja_env.globals.update(gettext=gettext)

@app.before_request
def make_session_permanent():
    session.permanent = True
    # app.permanent_session_lifetime = timedelta(minutes=5)


if __name__ == '__main__':
    # app.run(Network().get_node_management_ip(),port=5001)
    app.run(Network().get_node_management_ip(), port=5001, threaded=True)


