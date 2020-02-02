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

from PetaSAN.core.common.log import logger
from PetaSAN.backend.cluster.benchmark import Benchmark
from PetaSAN.backend.manage_node import ManageNode
from PetaSAN.core.security.basic_auth import requires_auth, authorization
from flask import Blueprint, render_template, session, request, json
from PetaSAN.backend.manage_pools import ManagePools

benchmark_controller = Blueprint('benchmark_controller', __name__)

list_err = "err"
list_warning = "warning"
list_success = "success"


@benchmark_controller.route('/benchmark', methods=['GET'])
@requires_auth
@authorization("ClusterBenchmark")
def benchmark_form():
    try:
        nodes = ManageNode()
        node_list = nodes.get_node_list()
        result = "ui_admin_benchmark_warning_message"

        # get pool_list


        manage_pool = ManagePools()
        pool_names = manage_pool.get_active_pools()

    # end get pools

        return render_template('admin/benchmark/cluster_benchmark_form.html', nodes=node_list, info=result, pools_list=sorted(pool_names))
    except Exception as e:
        session[list_err] = "ui_admin_error_loading_benchmark_page"


@benchmark_controller.route('/benchmark/run', methods=['GET'])
@requires_auth
@authorization("ClusterBenchmark")
def run_benchmark_test():
    if request.method == 'GET':
        try:
            # add pool
            clean_test_data = False
            clean = request.values['clean']
            pool = request.values['pool']
            test = request.values['test']
            threads_no = request.values['threads_no']
            duration = request.values['duration']
            clients = request.values['clients'].split(',')

            if clean == 'true':
                clean_test_data = True

            benchmark = Benchmark()
            # add pool name to the method
            process_id = benchmark.start(test, duration, threads_no, clients, pool, clean_test_data)
            logger.info("Benchmark Test Started")
            json_data = json.dumps(process_id)
            return json_data
        except Exception as e:
            return -1

@benchmark_controller.route('/benchmark/check/<process_id>', methods=['GET'])
@requires_auth
@authorization("ClusterBenchmark")
def check_process_id(process_id):
    if request.method == 'GET':
        try:
            benchmark = Benchmark()
            is_complete = benchmark.is_test_complete(process_id)
            if is_complete:
                logger.info("Benchmark Test Completed")
            json_data = json.dumps(is_complete)
            return json_data
        except Exception as e:
            return False

@benchmark_controller.route('/benchmark/report/<process_id>', methods=['GET'])
@requires_auth
@authorization("ClusterBenchmark")
def get_test_report(process_id):
    if request.method == 'GET':
        try:
            benchmark = Benchmark()
            report = benchmark.get_test_report(process_id)
            if report == None:
                return "-2"
            else:
                return report.write_json()
        except Exception as e:
            return -1