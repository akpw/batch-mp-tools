## Copyright (c) 2014 Arseniy Kuznetsov
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

import copyreg, types
import multiprocessing
from batchmp.commons.progressbar import progress_bar
from abc import ABCMeta, abstractmethod

class Task(metaclass = ABCMeta):
    ''' Represents an abstract TasksProcessor task
    '''
    def __init__(self, task_args):
        self.task_args = task_args

    def __call__():
        execute()

    @abstractmethod
    def execute(self):
        pass


class TasksProcessor:
    ''' Run tasks in a pool of processes
        Displays progress / tasks done
    '''
    def _process_task(self, task):
        result = task.execute()
        return result

    def process_tasks(self, tasks_queue, num_workers = None, quiet = False):
        tasks_done, num_tasks = 0, len(tasks_queue)
        cpu_core_time = 0.0
        if num_tasks > 0:
            if not num_workers:
                num_workers = multiprocessing.cpu_count()
            print('Processing {0} tasks with pool of {1} worker processes'.format(num_tasks, num_workers))
            # start showing progress
            with progress_bar() as p_bar:
                # init the pool and kick it off
                with multiprocessing.Pool(num_workers) as pool:
                    for res in pool.imap_unordered(self._process_task, tasks_queue):
                        if not quiet:
                            p_bar.info_msg = res[0][0]
                        cpu_core_time += res[1]
                        tasks_done += 1
                        p_bar.progress = tasks_done / num_tasks * 100

        # return overall time spent by the cpu cores
        return cpu_core_time


"""
    Python multiprocessing pickles stuff, and bound methods are not picklable
    The code below serves as a workaround, more at:
    http://bytes.com/topic/python/answers/552476-why-cant-you-pickle-instancemethods#edit2155350
"""
def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class

    if func_name.startswith('__') and not func_name.endswith('__'):
        cls_name = cls.__name__.lstrip('_')
        if cls_name:
            func_name = '_' + cls_name + func_name

    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)

copyreg.pickle(types.MethodType, _pickle_method, _unpickle_method)

