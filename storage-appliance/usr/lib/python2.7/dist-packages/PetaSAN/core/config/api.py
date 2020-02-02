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

import time
import random
from PetaSAN.core.entity.app_config import AppConfig
from PetaSAN.core.entity.maintenance import MaintenanceConfig, MaintenanceStatus
from PetaSAN.core.consul.base import BaseAPI
from PetaSAN.core.common.log import logger

from PetaSAN.core.common.CustomException import ConfigReadException
from PetaSAN.core.common.CustomException import ConfigWriteException

# App Settings
# CONF_FILE_PATH = '/opt/petasan/conf/petasan.conf'

# Ceph
# cluster_name = configuration().get_cluster_info().name
CEPH_CONF_PATH = '/etc/ceph/{}.conf'
CEPH_KEYRING_PATH = '/etc/ceph/{}.client.admin.keyring'
CEPH_MON_KEYRING = "{}.mon.keyring"
IMAGE_META_KEY = 'petasan-metada'
IMAGE_NAME_PREFIX = 'image-'

# Consul
CONSUL_BASE_PATH = 'PetaSAN'
CONSUL_NODES_PATH = CONSUL_BASE_PATH + '/Nodes/'
CONSUL_CONFIG_PATH = CONSUL_BASE_PATH + '/Config'
CONSUL_MAINTENANCE_CONFIG_PATH = CONSUL_BASE_PATH + '/Config/Maintenance'
CONSUL_MAINTENANCE_STATUS_PATH = CONSUL_BASE_PATH + '/Config/Maintenance/Status'
CONSUL_CONFIG_FILES_PATH = CONSUL_CONFIG_PATH + '/Files'
CONSUL_DISKS_PATH = CONSUL_BASE_PATH + '/Disks/'
CONSUL_DISK_POOLS_PATH = CONSUL_BASE_PATH + '/DiskPools/'
CONSUL_ASSIGNMENTS_PATH = CONSUL_BASE_PATH + '/Assignment/'
CONSUL_SESSION_PATH = CONSUL_BASE_PATH + '/Sessions/'
CONSUL_USER_PATH = CONSUL_BASE_PATH + '/Users/'
CONSUL_LEADERS_PATH = CONSUL_BASE_PATH + '/leaders/'
CONSUL_CLUSTER_INFO_PATH = CONSUL_BASE_PATH + '/Cluster_info'
CONSUL_SERVICES_PATH = CONSUL_BASE_PATH + '/Services/'

CONSUL_WATCH_TIME = '10s'
CONSUL_WATCH_SLEEP_MAX = 1

# MISC
LOCK_NEW_DISK_DELAY = 5
SIBLINGS_PATHS_DELAY = 4
DELAY_BEFORE_LOCK = 2
FAILURE_TIMEOUT_DURATION_MIN = 10

# Cluster files paths
CLUSTER_FILES_PATH = "/opt/petasan/"
CLUSTER_SCRIPTS_FILES_PATH = CLUSTER_FILES_PATH + "scripts/"
SERVICES_FILES_PATH = CLUSTER_FILES_PATH + "services/"
CLUSTER_INFO_FILE_PATH = CLUSTER_FILES_PATH + "config/cluster_info.json"
REPLACE_FILE_PATH = CLUSTER_FILES_PATH + "config/replace"
NODE_INFO_FILE_PATH = CLUSTER_FILES_PATH + "config/node_info.json"
NODE_CONFIG_BACKEND_IPS_SCRIPT = CLUSTER_SCRIPTS_FILES_PATH + "node_start_ips.py"
NODE_CREATE_MON_SCRIPT = CLUSTER_SCRIPTS_FILES_PATH + "create_mon.py"
NODE_CREATE_OSD_SCRIPT = CLUSTER_SCRIPTS_FILES_PATH + "create_osd.py"
NODE_CLEAN_SCRIPT = CLUSTER_SCRIPTS_FILES_PATH + "clean_ceph.py"
NODE_PRE_CONFIG_STORAGE_DISKS = CLUSTER_FILES_PATH + "PreConfigStorageDisks.json"
CLUSTER_CEPH_CONFIG_DIR_PATH = "/etc/ceph/"
MESSAGES_FILE_PATH = CLUSTER_FILES_PATH + "messages/en.txt"
CLUSTER_ADMIN_SCRIPTS_FILES_PATH = CLUSTER_SCRIPTS_FILES_PATH + "admin/"
CLUSTER_ADMIN_JOB_SCRIPTS_FILES_PATH = CLUSTER_SCRIPTS_FILES_PATH + "jobs/"
LOG_FILE = CLUSTER_FILES_PATH + "log/PetaSAN.log"
CONSUL_START_UP_SCRIPT_PATH = CLUSTER_SCRIPTS_FILES_PATH + 'consul_start_up.py'
CONSUL_CLIENT_START_UP_SCRIPT_PATH = CLUSTER_SCRIPTS_FILES_PATH + 'consul_client_start_up.py'
CONSUL_CREATE_CONF_SCRIPT = CLUSTER_SCRIPTS_FILES_PATH + 'create_consul_conf.py'
CONSUL_ENCRYPTION_KEY_SCRIPT = CLUSTER_SCRIPTS_FILES_PATH + 'read_ecryption_key.py'
CONSUL_STOP_SCRIPT_PATH = CLUSTER_SCRIPTS_FILES_PATH + 'consul_stop.py'
CONSUL_CLEAN_SCRIPT_PATH = CLUSTER_SCRIPTS_FILES_PATH + 'clean_consul.py'

START_UP_PETA_SERVICES_PATH = CLUSTER_SCRIPTS_FILES_PATH + 'start_petasan_services.py'
STOP_PETA_SERVICES_PATH = CLUSTER_SCRIPTS_FILES_PATH + 'stop_petasan_services.py'
CLUSTER_STATUS_FOR_JOIN_SCRIPT = CLUSTER_SCRIPTS_FILES_PATH + 'check_cluster_status_for_join.py'
KILL_CONSOLE_SCRIPT = CLUSTER_SCRIPTS_FILES_PATH + 'stop_console.py'

TUNING_DIR_PATH = "/opt/petasan/config/tuning/"
TUNING_TEMPLATES_DIR_PATH = TUNING_DIR_PATH + "templates/"
CURRENT_TUNINGS_PATH = TUNING_DIR_PATH + "current/"
LIO_TUNINGS_FILE_NAME = "lio_tunings"
CEPH_TUNINGS_FILE_NAME = "ceph_tunings"
POST_DEPLOY_SCRIPT_FILE_NAME = "post_deploy_script"

CRUSH_RULE_TEMPLATES_PATH = '/opt/petasan/config/crush/rule_templates/'
CRUSH_SAVE_PATH = '/opt/petasan/config/crush/backup/'

SYNC_SERVICE = 'files_sync.py'
PETASAN_SERVICE = 'iscsi_service.py'
WEB_MANAGEMENT_SERVICE = 'admin.py'
PETASAN_CONSOLE = 'console.py'
ADMIN_NODE_MANAGE_DISKS_SCRIPT = CLUSTER_ADMIN_SCRIPTS_FILES_PATH + "node_manage_disks.py"
ADMIN_DELETE_OSD_JOB_SCRIPT = CLUSTER_ADMIN_JOB_SCRIPTS_FILES_PATH + "delete_osd.py"
ADMIN_ADD_OSD_JOB_SCRIPT = CLUSTER_ADMIN_JOB_SCRIPTS_FILES_PATH + "add_osd.py"
ADMIN_ADD_JOURNAL_JOB_SCRIPT = CLUSTER_ADMIN_JOB_SCRIPTS_FILES_PATH + "add_journal.py"
ADMIN_DELETE_JOURNAL_JOB_SCRIPT = CLUSTER_ADMIN_JOB_SCRIPTS_FILES_PATH + "delete_journal.py"

ISCSI_SERVICE_SESSION_NAME = 'iSCSITarget'
LEADER_SERVICE_SESSION_NAME = 'ClusterLeader'
ASSIGNMENT_SESSION_NAME = 'AssignmentPaths'
COLLECT_STATE_DIR_PATH = "/opt/petasan/log/collect/"
COLLECT_STATE_SCRIPT_PATH = "/opt/petasan/scripts/util/collect_state.py"
ARPING_SCRIPT_PATH = "/opt/petasan/scripts/util/arping.py"
BENCHMARK_SCRIPT_PATH = "/opt/petasan/scripts/util/benchmark.py"
NODE_STRESS_JOB_SCRIPT_PATH = "/opt/petasan/scripts/jobs/benchmark/client_stress.py"
STORAGE_LOAD_JOB_SCRIPT_PATH = "/opt/petasan/scripts/jobs/benchmark/storage_load.py"
JOB_INFO_SCRIPT_PATH = "/opt/petasan/scripts/jobs/job_info.py"
DISK_PERFORMANCE_SCRIPT_PATH = "/opt/petasan/scripts/util/disk_performance.py"
MANAGE_NODE_DISK_SCRIPT_PATH = "/opt/petasan/scripts/admin/node_manage_disks.py"

ASSIGNMENTS_SCRIPT_PATH = "/opt/petasan/scripts/admin/reassignment_paths.py"
DELETE_POOL_SCRIPT_PATH = '/opt/petasan/scripts/util/delete_pool.py'
DELETE_Disk_SCRIPT_PATH = '/opt/petasan/scripts/util/delete_iscsi_disk.py'

ACTIVE_POOLS_SCRIPT_PATH = '/opt/petasan/scripts/util/list_active_pools.py'
ACTIVE_OSDS_SCRIPT_PATH = '/opt/petasan/scripts/util/list_active_osds.py'

# Notifications
NOTIFY_CLUSTER_USED_SPACE_PERCENT = 60
NOTIFY_POOL_USED_SPACE_PERCENT = 85

# Replication
CONSUL_REPLICATION_PATH = CONSUL_BASE_PATH + '/Replication/'
CONSUL_REPLICATION_JOBS_PATH = CONSUL_REPLICATION_PATH + 'Jobs/'
CONSUL_REPLICATION_ACTIVE_JOBS_PATH = CONSUL_REPLICATION_PATH + 'Active_Jobs/'
CONSUL_REPLICATION_LOGS_PATH = CONSUL_REPLICATION_PATH + 'Logs/'
CONSUL_REPLICATION_LAST_JOB_ID_PATH = CONSUL_REPLICATION_PATH + 'LAST_JOB_ID'
CONSUL_REPLICATION_FAILED_JOBS_PATH = CONSUL_REPLICATION_PATH + 'Failed_Jobs/'

DISK_META_SCRIPT_PATH = '/opt/petasan/scripts/util/disk_meta.py'
REPLICATION_SCRIPT_PATH = '/opt/petasan/scripts/backups/replication.py'
CRON_SCRIPT_PATH = '/opt/petasan/scripts/cron.py'
#CRON_SCRIPT_PATH = '/opt/petasan/scripts/cron/crontab.py'

REPLICATION_PROGRESS_SCRIPT_PATH = '/opt/petasan/scripts/backups/progress_updater.py'
REPLICATION_PIPE_READER_SCRIPT_PATH = '/opt/petasan/scripts/backups/pipe_reader.py'
REPLICATION_CLEAR_DISK_SCRIPT_PATH = '/opt/petasan/scripts/backups/clear_disk.py'
BACKFILL_SPEED_SCRIPT_PATH = '/opt/petasan/scripts/util/set_backfill_speed.py'
REPLICATION_KILL_JOB_PROCESSES_SCRIPT_PATH = '/opt/petasan/scripts/backups/kill_job_processes.py'
REPLICATION_SYNC_USERS_SCRIPT_PATH = '/opt/petasan/scripts/backups/sync_replication_users.py'

REPLICATION_TMP_FILE_PATH = '/opt/petasan/config/replication/'
REPLICATION_SSHKEY_FILE_PATH = '/opt/petasan/config/replication/{}_sshkey.txt'
REPLICATION_PROGRESS_COMP_FILE_PATH = '/opt/petasan/config/replication/{}_progress_comp.json'
REPLICATION_PROGRESS_UNCOMP_FILE_PATH = '/opt/petasan/config/replication/{}_progress_uncomp.json'
REPLICATION_PROGRESS_IMPORT_FILE_PATH = '/opt/petasan/config/replication/{}_progress_import.txt'
REPLICATION_MD5_1_FILE_PATH = '/opt/petasan/config/replication/{}_md5_1.txt'
REPLICATION_MD5_2_FILE_PATH = '/opt/petasan/config/replication/{}_md5_2.txt'
CONSUL_REPLICATION_DESTINATION_CLUSTERS_PATH = CONSUL_REPLICATION_PATH + 'Destination_Clusters/'

# Replication Users
CONSUL_REPLICATION_USERS_PATH = CONSUL_REPLICATION_PATH + 'Users/'
REPLICATION_USER_PRVKEY_FILE_PATH = REPLICATION_TMP_FILE_PATH + '{}_key'
REPLICATION_USER_PUBKEY_FILE_PATH = REPLICATION_TMP_FILE_PATH + '{}_key.pub'

DETECT_INTERFACES_SCRIPT_PATH = '/opt/petasan/scripts/detect-interfaces.sh'

KEEP_RESOURCES_FLAG_PATH = '/tmp/iscsi_keep_resources_flag'

# Caching
ADMIN_ADD_CACHE_JOB_SCRIPT = CLUSTER_ADMIN_JOB_SCRIPTS_FILES_PATH + 'add_cache.py'
ADMIN_DELETE_CACHE_JOB_SCRIPT = CLUSTER_ADMIN_JOB_SCRIPTS_FILES_PATH + 'delete_cache.py'



class ConfigAPI(object):
    def get_petasan_console(self):
        return PETASAN_CONSOLE

    def get_sync_file_service(self):
        return SYNC_SERVICE

    def get_petasan_service(self):
        return PETASAN_SERVICE

    def get_management_service(self):
        return WEB_MANAGEMENT_SERVICE

    def get_ceph_conf_path(self, cluster_name):
        return str(CEPH_CONF_PATH).format(cluster_name)

    def get_ceph_keyring_path(self, cluster_name):
        return str(CEPH_KEYRING_PATH).format(cluster_name)

    def get_ceph_mon_keyring(self, cluster_name):
        return str(CEPH_MON_KEYRING).format(cluster_name)

    def get_image_meta_key(self):
        return IMAGE_META_KEY

    def get_image_name_prefix(self):
        return IMAGE_NAME_PREFIX

    def get_consul_disks_path(self):
        return CONSUL_DISKS_PATH

    def get_consul_disk_pools_path(self):
        return CONSUL_DISK_POOLS_PATH

    def get_consul_assignment_path(self):
        return CONSUL_ASSIGNMENTS_PATH

    def get_consul_services_path(self):
        return CONSUL_SERVICES_PATH

    # get_consul_config_files_path
    def get_consul_config_files_path(self):
        return CONSUL_CONFIG_FILES_PATH

    def get_lock_new_disk_delay(self):
        return LOCK_NEW_DISK_DELAY

    # CONSUL_NODES_PATH
    def get_consul_nodes_path(self):
        return CONSUL_NODES_PATH

    def get_consul_leaders_path(self):
        return CONSUL_LEADERS_PATH

    def get_consul_watch_time(self):
        return CONSUL_WATCH_TIME

    def get_consul_watch_sleep_max(self):
        return CONSUL_WATCH_SLEEP_MAX

    def get_consul_start_up_script_path(self):
        return CONSUL_START_UP_SCRIPT_PATH

    def get_consul_client_start_up_script_path(self):
        return CONSUL_CLIENT_START_UP_SCRIPT_PATH

    def get_consul_stop_script_path(self):
        return CONSUL_STOP_SCRIPT_PATH

    def get_consul_clean_script_path(self):
        return CONSUL_CLEAN_SCRIPT_PATH

    def get_service_files_path(self):
        return SERVICES_FILES_PATH

    def get_collect_state_dir(self):
        return COLLECT_STATE_DIR_PATH

    def get_collect_state_script(self):
        return COLLECT_STATE_SCRIPT_PATH

    def disk_performance_script(self):
        return DISK_PERFORMANCE_SCRIPT_PATH

    def get_manage_node_disk_script(self):
        return MANAGE_NODE_DISK_SCRIPT_PATH

    """
    def read_from_file(self):
        conf_file = open(CONF_FILE_PATH,'r')
        j = conf_file.read().replace('\n','')
        conf_file.close()
        app_config = AppConfig()
        app_config.read_json(j)
        return app_config


    def write_to_file(self, app_config) :
        j = app_config.write_json()
        conf_file = open(CONF_FILE_PATH,'w')
        conf_file.write(j)
        conf_file.close()
    """

    def get_consul_session_path(self):
        return CONSUL_SESSION_PATH

    def get_user_path(self):
        return CONSUL_USER_PATH

    def read_app_config(self):
        app_config = AppConfig()
        try:
            cons = BaseAPI()
            j = cons.read_value(CONSUL_CONFIG_PATH)
            if j is None:
                # no config found, return empty object
                return app_config
            app_config.read_json(j)
            # logger.info("Success reading application config " + j)
        except Exception as e:
            logger.error("Error reading application config " + e.message)
            raise ConfigReadException("Error reading application config")
        return app_config

    def read_maintenance_config(self):
        maintenance_config = MaintenanceConfig()
        try:
            cons = BaseAPI()
            j = cons.read_value(CONSUL_MAINTENANCE_CONFIG_PATH)
            if j is None:
                # no config found, return empty object
                return maintenance_config
            maintenance_config.read_json(j)
        except Exception as e:
            logger.error("Error reading maintenance config " + e.message)
            raise ConfigReadException("Error reading maintenance config")
        return maintenance_config

    def read_maintenance_status(self):
        maintenance_status = MaintenanceStatus()
        try:
            cons = BaseAPI()
            j = cons.read_value(CONSUL_MAINTENANCE_STATUS_PATH)
            if j is None:
                # no config found, return empty object
                return maintenance_status
            maintenance_status.read_json(j)
        except Exception as e:
            logger.error("Error reading maintenance status " + e.message)
            raise ConfigReadException("Error reading maintenance status")
        return maintenance_status

    def write_app_config(self, app_config):
        """
        @type app_config: AppConfig
        """
        try:
            j = app_config.write_json()
            cons = BaseAPI()
            cons.write_value(CONSUL_CONFIG_PATH, j)
            logger.info("Success saving application config ")
        except Exception as e:
            logger.error("Error saving application config " + e.message)
            raise ConfigWriteException("Error saving application config")
        return

    def write_maintenance_config(self, maintenance_config):

        try:
            j = maintenance_config.write_json()
            cons = BaseAPI()
            cons.write_value(CONSUL_MAINTENANCE_CONFIG_PATH, j)
            logger.info("Success saving application config ")
        except Exception as e:
            logger.error("Error saving application config " + e.message)
            raise ConfigWriteException("Error saving application config")
        return

    def write_maintenance_status(self, maintenance_status):

        try:
            j = maintenance_status.write_json()
            cons = BaseAPI()
            cons.write_value(CONSUL_MAINTENANCE_STATUS_PATH, j)
            logger.info("Success saving application config ")
        except Exception as e:
            logger.error("Error saving application config " + e.message)
            raise ConfigWriteException("Error saving application config")
        return

    def delete_app_config(self):
        try:
            cons = BaseAPI()
            cons.delete_key(CONSUL_CONFIG_PATH)
        except Exception as e:
            pass
        return

    def get_cluster_info_file_path(self):
        return CLUSTER_INFO_FILE_PATH

    def get_node_info_file_path(self):
        return NODE_INFO_FILE_PATH

    def get_node_start_ips_script_path(self):
        return NODE_CONFIG_BACKEND_IPS_SCRIPT

    def get_cluster_files_path(self):
        return CLUSTER_FILES_PATH

    def get_cluster_ceph_dir_path(self):
        return CLUSTER_CEPH_CONFIG_DIR_PATH

    def get_cluster_admin_job_scripts(self):
        return CLUSTER_ADMIN_SCRIPTS_FILES_PATH

    def get_node_create_mon_script_path(self):
        return NODE_CREATE_MON_SCRIPT

    def get_node_create_osd_script_path(self):
        return NODE_CREATE_OSD_SCRIPT

    def get_node_clean_script_path(self):
        return NODE_CLEAN_SCRIPT

    def get_consul_create_conf_script(self):
        return CONSUL_CREATE_CONF_SCRIPT

    def get_consul_encryption_key_script(self):
        return CONSUL_ENCRYPTION_KEY_SCRIPT

    def get_consul_cluster_info_path(self):
        return CONSUL_CLUSTER_INFO_PATH

    def get_startup_petasan_services_path(self):
        return START_UP_PETA_SERVICES_PATH

    def get_stop_petasan_services_path(self):
        return STOP_PETA_SERVICES_PATH

    def get_cluster_status_for_join_path(self):
        return CLUSTER_STATUS_FOR_JOIN_SCRIPT

    def get_kill_console_script_path(self):
        return KILL_CONSOLE_SCRIPT

    def get_replace_file_path(self):
        return REPLACE_FILE_PATH

    def get_siblings_paths_delay(self):
        return SIBLINGS_PATHS_DELAY

    def get_average_delay_before_lock(self):
        return DELAY_BEFORE_LOCK

    def get_messages_file_path(self):
        return MESSAGES_FILE_PATH

    def get_admin_manage_node_script(self):
        return ADMIN_NODE_MANAGE_DISKS_SCRIPT

    def get_admin_delete_osd_job_script(self):
        return ADMIN_DELETE_OSD_JOB_SCRIPT

    def get_admin_add_osd_job_script(self):
        return ADMIN_ADD_OSD_JOB_SCRIPT

    def get_admin_add_journal_job_script(self):
        return ADMIN_ADD_JOURNAL_JOB_SCRIPT

    def get_admin_delete_journal_job_script(self):
        return ADMIN_DELETE_JOURNAL_JOB_SCRIPT

    def get_log_file_path(self):
        return LOG_FILE

    def get_iscsi_service_session_name(self):
        return ISCSI_SERVICE_SESSION_NAME

    def get_leader_service_session_name(self):
        return LEADER_SERVICE_SESSION_NAME

    def get_assignment_session_name(self):
        return ASSIGNMENT_SESSION_NAME

    def get_notify_cluster_used_space_percent(self):
        return NOTIFY_CLUSTER_USED_SPACE_PERCENT

    def get_notify_pool_used_space_percent(self):
        return NOTIFY_POOL_USED_SPACE_PERCENT

    def get_tuning_templates_dir_path(self):
        return TUNING_TEMPLATES_DIR_PATH

    def get_current_tunings_path(self):
        return CURRENT_TUNINGS_PATH

    def get_lio_tunings_file_name(self):
        return LIO_TUNINGS_FILE_NAME

    def get_ceph_tunings_file_name(self):
        return CEPH_TUNINGS_FILE_NAME

    def get_post_deploy_script_file_name(self):
        return POST_DEPLOY_SCRIPT_FILE_NAME

    def get_arping_script_path(self):
        return ARPING_SCRIPT_PATH

    def get_benchmark_script_path(self):
        return BENCHMARK_SCRIPT_PATH

    def get_node_stress_job_script_path(self):
        return NODE_STRESS_JOB_SCRIPT_PATH

    def get_storage_load_job_script_path(self):
        return STORAGE_LOAD_JOB_SCRIPT_PATH

    def get_job_info_script_path(self):
        return JOB_INFO_SCRIPT_PATH

    def get_failure_timeout_duration_min(self):
        return FAILURE_TIMEOUT_DURATION_MIN

    def get_node_pre_config_disks(self):
        return NODE_PRE_CONFIG_STORAGE_DISKS

    def get_assignment_script_path(self):
        return ASSIGNMENTS_SCRIPT_PATH

    def get_crush_save_path(self):
        return CRUSH_SAVE_PATH

    def get_crush_rule_templates_path(self):
        return CRUSH_RULE_TEMPLATES_PATH

    def get_delete_pool_scipt(self):
        return DELETE_POOL_SCRIPT_PATH

    def get_active_pools_script(self):
        return ACTIVE_POOLS_SCRIPT_PATH

    def get_active_osds_script(self):
        return ACTIVE_OSDS_SCRIPT_PATH

    def get_delete_disk_scipt(self):
        return DELETE_Disk_SCRIPT_PATH

    # Replication
    # ===========
    def get_consul_replication_path(self):
        return CONSUL_REPLICATION_PATH

    def get_consul_replication_jobs_path(self):
        return CONSUL_REPLICATION_JOBS_PATH

    def get_consul_replication_active_jobs_path(self):
        return CONSUL_REPLICATION_ACTIVE_JOBS_PATH

    def get_consul_replication_logs_path(self):
        return CONSUL_REPLICATION_LOGS_PATH

    def get_consul_replication_last_job_id_path(self):
        return CONSUL_REPLICATION_LAST_JOB_ID_PATH

    def get_consul_replication_failed_jobs_path(self):
        return CONSUL_REPLICATION_FAILED_JOBS_PATH

    def get_disk_meta_script_path(self):
        return DISK_META_SCRIPT_PATH

    def get_replication_script_path(self):
        return REPLICATION_SCRIPT_PATH

    def get_cron_script_path(self):
        return CRON_SCRIPT_PATH

    def get_replication_progress_script_path(self):
        return REPLICATION_PROGRESS_SCRIPT_PATH

    def get_replication_pipe_reader_script_path(self):
        return REPLICATION_PIPE_READER_SCRIPT_PATH

    def get_replication_clear_disk_script_path(self):
        return REPLICATION_CLEAR_DISK_SCRIPT_PATH

    def get_backfill_speed_script_path(self):
        return BACKFILL_SPEED_SCRIPT_PATH

    def get_replication_tmp_file_path(self):
        return REPLICATION_TMP_FILE_PATH

    def get_replication_sshkey_file_path(self, active_job_id=""):
        # Generate a random value between 1 and 999999 #
        random_no = str(random.randint(1,1000000))

        time_stamp = str(int(round(time.time())))
        path = time_stamp + "_" + random_no

        if len(active_job_id) > 0:
            path = active_job_id + "_" + time_stamp + "_" + random_no

        return str(REPLICATION_SSHKEY_FILE_PATH).format(path)

    def get_replication_progress_comp_file_path(self, active_job_id):
        return str(REPLICATION_PROGRESS_COMP_FILE_PATH).format(active_job_id)

    def get_replication_progress_uncomp_file_path(self, active_job_id):
        return str(REPLICATION_PROGRESS_UNCOMP_FILE_PATH).format(active_job_id)

    def get_replication_progress_import_file_path(self, active_job_id):
        return str(REPLICATION_PROGRESS_IMPORT_FILE_PATH).format(active_job_id)

    def get_replication_md5_1_file_path(self, active_job_id):
        return str(REPLICATION_MD5_1_FILE_PATH).format(active_job_id)

    def get_replication_md5_2_file_path(self, active_job_id):
        return str(REPLICATION_MD5_2_FILE_PATH).format(active_job_id)

    def get_consul_replication_destination_clusters_path(self):
        return CONSUL_REPLICATION_DESTINATION_CLUSTERS_PATH

    def get_consul_replication_users_path(self):
        return CONSUL_REPLICATION_USERS_PATH

    def get_replication_user_prvkey_file_path(self):
        time_stamp = str(int(round(time.time())))
        return REPLICATION_USER_PRVKEY_FILE_PATH.format(time_stamp)

    def get_replication_user_pubkey_file_path(self):
        time_stamp = str(int(round(time.time())))
        return REPLICATION_USER_PUBKEY_FILE_PATH.format(time_stamp)

    def get_replication_kill_job_processes_file_path(self):
        return REPLICATION_KILL_JOB_PROCESSES_SCRIPT_PATH

    def get_replication_sync_users_script_path(self):
        return REPLICATION_SYNC_USERS_SCRIPT_PATH

    def get_detect_interfaces_script_path(self):
        return DETECT_INTERFACES_SCRIPT_PATH

    def get_keep_resources_flag_path(self):
        return KEEP_RESOURCES_FLAG_PATH

    def get_admin_add_cache_job_script(self):
        return ADMIN_ADD_CACHE_JOB_SCRIPT

    def get_admin_delete_cache_job_script(self):
        return ADMIN_DELETE_CACHE_JOB_SCRIPT


