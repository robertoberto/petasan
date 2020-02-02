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

from PetaSAN.core.entity.job import JobType
from PetaSAN.core.cluster.job_manager import JobManager
from PetaSAN.core.common.log import logger
from time import sleep
from PetaSAN.core.config.api import ConfigAPI
from PetaSAN.core.entity.benchmark import BenchmarkResult, RadosResult, SarResult
from PetaSAN.core.ssh.ssh import ssh
from PetaSAN.backend.manage_node import ManageNode
from PetaSAN.core.ceph.api import CephAPI
from PetaSAN.core.common.sar import Sar
from PetaSAN.core.common.enums import RadosBenchmarkType, NodeStatus, BlockSize


class Benchmark(object):
    output_split_text = "##petasan##"

    def __init__(self):
        self.type = -1
        self.stress_duration = -1
        self.threads = -1
        self.clients = []
        self.storage_nodes = []
        self.write_jobs = {}
        self.read_jobs = {}
        self.wait_for_collect_state = 0
        self.report = None
        self.pool = None
        pass

    def start(self, type, duration_sec, threads, clients,pool,cleanup):
        job_manager = JobManager()
        clients = "" + ",".join(clients) + ""
        for j in job_manager.get_running_job_list():
            if j.type == JobType.BENCHMANAGER:
                logger.info("Cannot start benchmark manager there is a job already running.")
                return -1
        cleanup_val = 1
        if not cleanup:
            cleanup_val = 0
        params = '-d {} -t {} -type {} -c {} -p {} --cleanup {}'.format(duration_sec, threads, type, clients,pool,cleanup_val)
        id = job_manager.add_job(JobType.BENCHMANAGER, params)

        return id


    def sar_stats(self, duration):
        return Sar().run(duration)


    def rados_benchmark(self, block_size, is_type_write, duration_sec, threads, pool):
        ceph_api = CephAPI()

        if is_type_write:
            return ceph_api.rados_write(duration_sec, threads, block_size, pool)
        else:
            return ceph_api.rados_read(duration_sec, threads, pool)


    def manager(self, test_type, duration_sec, threads, clients,pool,cleanup):

        # CephAPI().create_rados_test_pool()
        logger.debug("Benchmark manager request.")
        logger.debug(clients)
        try:
            self.type = int(test_type)
            # Duration of write and read stress test
            self.stress_duration = duration_sec / 2
            self.threads = threads
            # None storage nodes
            self.clients = clients
            # The span of time to wait between run rados test and collect state of storage nodes
            self.wait_for_collect_state = self.stress_duration / 4
            # Duration of collect node state
            self.state_duration = self.stress_duration / 2
            # pool
            self.pool = pool

            # running cleanup before the test, there will not be a cleanup file with written objects
            # will iterate for all objects in pool, very slow
            # self.__cleanup()

            nodes = ManageNode().get_node_list()
            # Get available storage nodes
            for node in nodes:
                if not node.name in clients and node.status == NodeStatus.up and node.is_storage:
                    self.storage_nodes.append(str(node.name))
                    print self.storage_nodes

            if len(self.storage_nodes) == 0 and \
                    (self.type == RadosBenchmarkType.four_mg_Throughput or self.type == RadosBenchmarkType.four_kb_iops):
                raise Exception("Cannot complete rados benchmark. No storage nodes available for run test.")

            logger.debug(self.storage_nodes)
            if self.type== RadosBenchmarkType.four_mg_Throughput or self.type == RadosBenchmarkType.four_kb_iops:
                self.report = BenchmarkResult()
                logger.info("Benchmark start rados write.")
                self.__write()
                logger.info("Benchmark start rados read.")
                self.__read()
                logger.info("Benchmark finished.")
                return self.report

            else:
                # TODO
                pass
        except Exception as e:
            logger.exception(e.message)
      
        finally:
            #CephAPI().delete_rados_test_pool()
            if cleanup:
                self.__cleanup()

  
    def __cleanup(self):
        cmd = ConfigAPI().get_benchmark_script_path() + ' clean -p ' + self.pool 
        for node in self.clients:
            try:
                # run clean as synchronous command
                logger.info('Running benchmark clean command on node:' + node + '  cmd:' + cmd)
                ssh().exec_command(node, cmd)
            except Exception as e:
                logger.error('Error running benchmark clean command on node:' + node)
                

    def __write(self):
        size = BlockSize().four_kb
        if self.type == RadosBenchmarkType.four_mg_Throughput:
            size = BlockSize().four_mg
        # Run rados benchmark on selected nodes
        for node in self.clients:
            cmd = "python " + ConfigAPI().get_node_stress_job_script_path() + " -d {} -t {} -b {} -m w -p {}".format(
                self.stress_duration,
                self.threads, size, self.pool)
            logger.info("Run rados write cmd on node {} : ".format(node) + cmd)
            out, err = ssh().exec_command(node, cmd)
            # get job id from output and assign to its node
            if err.startswith("Warning") or not err:
                self.write_jobs[int(out)] = node

        logger.info("Wait time before collect storage state.")
        sleep(self.wait_for_collect_state)

        # Get state of storage nodes
        for node in self.storage_nodes:
            cmd = "python " + ConfigAPI().get_storage_load_job_script_path() + " -d {} ".format(self.state_duration)
            out, err = ssh().exec_command(node, cmd)
            logger.info("Run sar state cmd on node {} : ".format(node) + cmd)
            if err.startswith("Warning") or not err:
                self.write_jobs[int(out)] = node
        # Wait to complete all jobs
        sleep(self.stress_duration - self.wait_for_collect_state)
        # Check the completed jobs and get the output
        while (len(self.write_jobs) > 0):
            remove_job_ids = []
            for job_id, node_name in self.write_jobs.iteritems():
                cmd = "python " + ConfigAPI().get_job_info_script_path() + " -id {} -t {}".format(job_id, 1)
                out, err = ssh().exec_command(node_name, cmd)
                # Job completed
                if int(out) == 1:
                    remove_job_ids.append(job_id)
                    cmd = "python " + ConfigAPI().get_job_info_script_path() + " -id {} -t {}".format(job_id, 2)
                    out, err = ssh().exec_command(node_name, cmd)
                    logger.debug("Get job output by cmd {} from node {} ".format(cmd,node_name) )
                    logger.debug("Output is {} ".format(out))
                    # job passed and get our output
                    if out.startswith(self.output_split_text) or out.find(self.output_split_text) > -1:
                        out = out.split(self.output_split_text)[1]
                else:
                    continue
                # Get rados IOPs output
                if node_name in self.clients:
                    rados_rs = RadosResult()
                    if out:
                        rados_rs.load_json(out)
                        self.report.write_iops += rados_rs.iops
                        self.report.write_throughput += rados_rs.throughput
                elif node_name in self.storage_nodes:
                    # Get sar output
                    sar_rs = SarResult()
                    sar_rs.load_json(out)
                    self.report.write_nodes.append(sar_rs)

            # Remove completed jobs
            for i in remove_job_ids:
                self.write_jobs.pop(i)
            if len(self.read_jobs) > 0:
                sleep(5)

    def __read(self):
        # Run rados benchmark on selected nodes
        for node in self.clients:
            cmd = "python " + ConfigAPI().get_node_stress_job_script_path() + " -d {} -t {}  -m r -p {}".format(
                self.stress_duration,
                self.threads,self.pool)
            logger.info("Run rados read cmd on node {} : ".format(node) + cmd)
            out, err = ssh().exec_command(node, cmd)
            # get job id from output and assign to its node
            if not err:
                self.read_jobs[int(out)] = node

        logger.info("Wait time before collect node state.")
        sleep(self.wait_for_collect_state)

        # Get state of storage nodes
        for node in self.storage_nodes:
            cmd = "python " + ConfigAPI().get_storage_load_job_script_path() + " -d {} ".format(self.state_duration)
            out, err = ssh().exec_command(node, cmd)
            logger.info("Run sar state cmd on node {} : ".format(node) + cmd)
            if not err:
                self.read_jobs[int(out)] = node
        # Wait to complete all jobs
        sleep(self.stress_duration - self.wait_for_collect_state)
        # Check the completed jobs and get the output
        while (len(self.read_jobs) > 0):
            remove_job_ids = []
            for job_id, node_name in self.read_jobs.iteritems():
                cmd = "python " + ConfigAPI().get_job_info_script_path() + " -id {} -t {}".format(job_id, 1)
                out, err = ssh().exec_command(node_name, cmd)
                # Job completed
                if int(out) == 1:
                    remove_job_ids.append(job_id)
                    cmd = "python " + ConfigAPI().get_job_info_script_path() + " -id {} -t {}".format(job_id, 2)
                    out, err = ssh().exec_command(node_name, cmd)
                    logger.debug("Get job output by cmd {} from node {} ".format(cmd,node_name) )
                    logger.debug("Output is {} ".format(out))
                    # job passed and get our output
                    if out.startswith(self.output_split_text) or out.find(self.output_split_text) > -1:
                        out = out.split(self.output_split_text)[1]
                else:
                    continue
                # Get rados IOPs output
                if node_name in self.clients:
                    rados_rs = RadosResult()
                    if out:
                        rados_rs.load_json(out)
                        self.report.read_iops += rados_rs.iops
                        self.report.read_throughput += rados_rs.throughput
                elif node_name in self.storage_nodes:
                    # Get sar output
                    sar_rs = SarResult()
                    if out:
                        sar_rs.load_json(out)
                        self.report.read_nodes.append(sar_rs)

            # Remove completed jobs
            for i in remove_job_ids:
                self.read_jobs.pop(i)
            if len(self.read_jobs) > 0:
                sleep(5)


    def is_test_complete(self, id):
        return JobManager().is_done(id)


    def get_test_report(self, id):
        try:
            result = JobManager().get_job_output(id)
            if result.startswith(self.output_split_text) or result.find(self.output_split_text) > -1:
                result = result.split(self.output_split_text)[1]
            else:
                return None
            report = BenchmarkResult()
            report.load_json(result)
        except:
            return None
        return report
