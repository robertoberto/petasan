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


from PetaSAN.core.entity.job import *
from PetaSAN.core.common.log import logger

import os
import sys
import time
from os import listdir
from os.path import isfile
from os.path import getctime
import signal
import threading

JOBS_PATH = '/opt/petasan/jobs'


TOKEN_SEP= ':'
PARAM_SEP= '@'


# jobs file:
# JOBS_PATH/pid:job_type:param1@param2..:start_timestamp.job



class PIDWaitThread(threading.Thread):

    def __init__(self,pid):
        threading.Thread.__init__(self)
        self.pid = pid
        self.setDaemon(True)

    def run(self):
        os.waitpid(self.pid, 0)



class JobManager(object):

    # signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    def add_job(self, type, params):

        """
        try:
            #if threading.current_thread().name == 'MainThread' :
            signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        except:
            pass
        """

        script = job_scripts[type]
        logger.info('script')
        logger.info(script)
        logger.info('params')
        logger.info(params)

        if script is None or len(script.split()) == 0 :
            return -1

        newpid = os.fork()
        if newpid == 0:
            pid = os.getpid()
            filename =  JOBS_PATH + '/' + self._new_job_filename(pid,type,params)
            file = open(filename, 'w')
            os.dup2(file.fileno(), sys.stdout.fileno())
            os.execv(script.split()[0], script.split() + params.split())


        time.sleep(0.1)

        # threading.Thread(target=self.wait_for_pid,args=(self,newpid) ).start()
        wait_thread = PIDWaitThread(newpid)
        wait_thread.start()

        return newpid


    def get_job_list(self):
        jobs = []
        files = self._get_job_filenames()
        for f in files:
             jobs.append(self._get_job(f))

        return jobs

    def get_running_job_list(self):
        running_jobs = []
        jobs = self.get_job_list()
        for job in jobs :
            if job.is_running:
                running_jobs.append(job)
        return running_jobs

    """
    DOCSTRING : this function is called to get running jobs of certain type.
    Args : job_type
    Returns : dictionary of running jobs of job_type
    """
    def get_running_jobs_by_type(self,job_type):
        running_jobs_dict = {}
        running_jobs = []
        jobs = self.get_job_list()
        for job in jobs :
            if job.is_running and job.type == job_type:
                running_jobs.append(job)
        running_jobs_dict[job_type] = running_jobs
        return running_jobs_dict


    def is_done(self, pid):
        return not self._is_job_running(pid)


    def get_job_output(self, pid):
        filename = self._get_job_filename(pid)
        if filename is None:
            return None
        try:
            file = open(JOBS_PATH + '/' + filename, 'r')
            str = file.read()
            return str
        except:
            pass
        return None


    def remove_job(self, id):
        if self._is_job_running(id) :
            self._kill_job(id)

        filename = self._get_job_filename(id)
        if filename is None:
            return
        try:

            os.remove(JOBS_PATH + '/' + filename)
        except:
            pass
        return


    def remove_jobs_since(self, sec):
        remove_jobs = []
        jobs = self.get_job_list()
        for job in jobs :
            if sec < job.started_since :
                remove_jobs.append(job)
        for job in remove_jobs :
            self.remove_job(job.id)
        return


    def _get_job(self,filename):

        if not isfile(JOBS_PATH + '/' + filename):
            return None
        tokens = filename[:-4].split(TOKEN_SEP)
        if len(tokens) !=  4:
            return None

        job = Job()
        job.id = tokens[0]
        job.type = tokens[1]
        job.params = tokens[2].replace(PARAM_SEP,' ')
         #job.started_since = self._get_started_since(filename)
        job.started_since =  int(time.time() - int(tokens[3]))
        job.is_running = self._is_job_running(job.id)

        return job

    def _get_job_filenames(self):
        filenames = []
        for f in listdir(JOBS_PATH):
            if isfile(JOBS_PATH + '/' + f) and f.endswith('.job'):
                filenames.append(f)
        return filenames


    def _get_job_filename(self,pid):
        files = self._get_job_filenames()
        for f in files:
            if f.startswith( str(pid)) :
                return f
        return None


    def _new_job_filename(self,pid,type,params):
        filename = str(pid) + TOKEN_SEP + type + TOKEN_SEP

        #filename += params.replace(' ',PARAM_SEP)
        if 0 < len( params.split()) :
            for param in params.split()[:-1]:
                filename += param + PARAM_SEP
            filename += params.split()[-1]
        else :
            filename += PARAM_SEP

        filename += TOKEN_SEP + str( int(time.time()))
        filename += '.job'
        return filename


    def _get_started_since(self,filename):
        if not isfile(JOBS_PATH + '/' + filename):
            return -1
        t1 = getctime(JOBS_PATH + '/' + filename)
        t2 = time.time()
        return t2 - t1


    def _is_job_running(self,pid):
        return os.path.exists('/proc/'+ str(pid))


    def _kill_job(self,pid):
        try:
            if self._is_job_running(pid)  :
                os.kill(pid, signal.SIGKILL)
        except:
            return
        return









'''
  def redirect_output(self):

        pid = os.getpid()
        file_name =  JOBS_PATHS + '/' + str(pid) + 'ADD_DISK.job'
        print "file_name is " + file_name
        file = open(file_name, 'w')
        print os.path.getctime(file_name)
        os.dup2(file.fileno(), sys.stdout.fileno())
        #os.setsid()

def test():
    #cmd = 'find . /root'
    cmd = CMD
    sub = subprocess.Popen(cmd.split(), shell = False,preexec_fn=redirect_output)

    # the pid to return
    pid = sub.pid

    # we need to avoid zombies. This happens if child terminates but not the parent and
    # parent does not read the exit code of the child so child process table is not cleaned up
    # we need either to call wait() or poll or delete reference of subprocess object

    # delete reference works for python 3 not 2.7
    # del sub
    # gc.collect()

    # spwan thread to handle wait
    threading.Thread(target=sub.wait).start()

    return pid

'''



'''
def handleSIGCHLD(x,y):
  os.waitpid(-1, os.WNOHANG)

signal.signal(signal.SIGCHLD, handleSIGCHLD)
signal.signal(signal.SIGCHLD, signal.SIG_IGN)

'''

'''
jm = JobManager()
jm.remove_jobs_since(120)

id = jm.add_job(JobType.TEST,"param1   param2")
print 'id is ' + str(id)


jm.get_job_list()


while not jm.is_done(id) :
  print "job still running"
  jm.get_job_list()
  time.sleep(5)

jm.get_job_list()
print jm.get_job_output(id)
'''