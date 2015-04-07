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


import copyreg, types, datetime, math, multiprocessing
from abc import ABCMeta, abstractmethod
from batchmp.commons.progressbar import progress_bar


class Task(metaclass = ABCMeta):
    ''' Represents an abstract TasksProcessor task
    '''
    @abstractmethod
    def execute(self):
        return TaskResult()

class TaskResult:
    ''' Represents a  TasksProcessor task result
    '''
    def __init__(self):
        self._task_steps_info_msgs = []
        self._task_steps_durations = []

    def add_task_step_duration(self, step_duration):
        self._task_steps_durations.append(step_duration)

    def add_task_step_info_msg(self, step_info_msg):
        self._task_steps_info_msgs.append(step_info_msg)

    def add_report_msg(self, processed_fpath):
        td = datetime.timedelta(seconds = math.ceil(self.task_duration * 100)/100)
        self.add_task_step_info_msg('Done processing\n {0}\n in {1}'.format(
                                                        processed_fpath, str(td).rstrip('0')))
    @property
    def task_output(self):
        task_output = None
        for info_msg in self._task_steps_info_msgs:
            task_output = '{0}{1}{2}'.format(task_output if task_output else '',
                                                '\n' if task_output else '',
                                                info_msg)
        return task_output

    @property
    def task_duration(self):
        task_duration = 0.0
        for step_duration in self._task_steps_durations:
            task_duration += step_duration
        return task_duration


class TasksProcessor:
    ''' Run command line Tasks, sequentially or in a pool of processes
        Displays progress / tasks done
    '''
    def _process_task(self, task):
        result = task.execute()
        return result

    def process_tasks(self, tasks_queue, serial_exec = False, num_workers = None, quiet = False):
        cpu_core_time = 0.0
        num_tasks = len(tasks_queue)
        serial_exec = serial_exec or num_tasks == 1
        if num_tasks > 0:
            tasks_done = 0

            # Pre-processing msgs
            if serial_exec:
                print('Processing {0} {1}'.format(num_tasks,
                                                        'task' if num_tasks == 1 else 'tasks sequentially'))
            else:
                if not num_workers:
                    num_workers = multiprocessing.cpu_count()
                print('Processing {0} tasks with pool of {1} worker processes'.format(num_tasks, num_workers))

            # start showing progress
            with progress_bar() as p_bar:
                def _show_progress():
                    nonlocal cpu_core_time, tasks_done
                    if not quiet:
                        p_bar.info_msg = result.task_output
                    cpu_core_time += result.task_duration
                    tasks_done += 1
                    p_bar.progress = tasks_done / num_tasks * 100

                if serial_exec:
                    # just loop through the queue of tasks
                    for task in tasks_queue:
                        result = self._process_task(task)
                        _show_progress()
                else:
                    # init the pool and kick it off
                    with multiprocessing.Pool(num_workers) as pool:
                        for result in pool.imap_unordered(self._process_task, tasks_queue):
                            _show_progress()

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

