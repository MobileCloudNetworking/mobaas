# Copyright 2014 Zuercher Hochschule fuer Angewandte Wissenschaften
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

__author__ = 'andy'

import multiprocessing

from mcn.sm import LOG


class Executor(multiprocessing.Process):
    def __init__(self, group_name, task_queue, result_queue):
        multiprocessing.Process.__init__(self)
        LOG.debug('executor: ' + self.name + ' is part of group: ' + group_name)
        self.group_name = group_name
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        super(Executor, self).run()
        task = self.task_queue.get()
        LOG.debug('task received')
        #blocking op
        LOG.debug('running task...')
        res = task.run()
        LOG.debug('sending result...')
        self.result_queue.put(res)

class ProMgr():
    def __init__(self, num_executors=1):
        multiprocessing.log_to_stderr(LOG.level)
        self.num_executors = num_executors  # should be a multiple of cores multiprocessing.cpu_count() * 2
        self.executors = []

        # create i/o queues
        LOG.debug('creating task in queues...')
        self.create_tasks = multiprocessing.Queue()
        self.deploy_tasks = multiprocessing.Queue()
        self.retrieve_tasks = multiprocessing.Queue()
        self.destroy_tasks = multiprocessing.Queue()

        LOG.debug('creating task return queues...')
        self.create_ret_vals = multiprocessing.Queue()
        self.deploy_ret_vals = multiprocessing.Queue()
        self.retrieve_ret_vals = multiprocessing.Queue()
        self.destroy_ret_vals = multiprocessing.Queue()

    def run(self):
        LOG.debug('creating executors...')
        self.executors = self.executors + [ Executor('creator', self.create_tasks, self.create_ret_vals) for i in xrange(self.num_executors)]
        self.executors = self.executors + [ Executor('deployer', self.deploy_tasks, self.deploy_ret_vals) for i in xrange(self.num_executors)]
        self.executors = self.executors + [ Executor('retriever', self.retrieve_tasks, self.retrieve_ret_vals) for i in xrange(self.num_executors)]
        self.executors = self.executors + [ Executor('destroyer', self.destroy_tasks, self.destroy_ret_vals) for i in xrange(self.num_executors)]

        LOG.debug('number of executors to start: ' + str(len(self.executors)))
        for executor in self.executors:
            executor.start()
