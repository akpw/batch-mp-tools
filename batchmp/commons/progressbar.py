# coding=utf8
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


''' A simple single-line console progress bar
    Displays progress by fractions of 10%
    Supports premature stops & info messages during execution
'''
import sys, time
from bisect import bisect as bs
import threading, queue
from contextlib import contextmanager


@contextmanager
def progress_bar(starts_from = 0):
    ''' Enables usage via a runtime context
    '''
    p_bar = CmdProgressBar(starts_from)
    p_bar.start()
    try:
        yield p_bar
    finally:
        p_bar.stop()


class CmdProgressBarUpdateTypes:
    UPDATE_PROGRESS = 0
    UPDATE_MSG = 1


class CmdProgressBar(object):
    def __init__(self, start_from=0):
        self._queue = queue.Queue(1)  # used to communicate with the worker thread
        self._end_event = threading.Event()  # used to exit

        self.progress = start_from # access via property, for validation $ enqueuing
        self._info_msg = None

        self._bar_thread = threading.Thread(target=self._show_progress,
                                            args=(start_from, self._end_event, self._queue,))
        self._bar_thread.daemon = True

    @property
    def info_msg(self):
        return self._info_msg
    @info_msg.setter
    def info_msg(self, value):
        self._queue.put((CmdProgressBarUpdateTypes.UPDATE_MSG, value))
        self._info_msg = value

    @property
    def progress(self):
        return self._progress
    @progress.setter
    def progress(self, value):
        # unless in stopping mode, set & enqueue
        if not self._end_event.is_set():
            if value < 0: value = 0
            if value > 100: value = 100
            self._queue.put((CmdProgressBarUpdateTypes.UPDATE_PROGRESS, value))
            self._progress = value

    # the worker thread method
    @staticmethod
    def _show_progress(last_known_progress, end_event, queue):
        progress_values = [i for i in range(0, 110, 10)]  # [0, 10, ..., 100]
        chars = '|/-\\'
        msg = None
        while True:
            if not queue.full():
                # nothing in the queue yet, keep showing the last known progres
                progress = last_known_progress
            else:
                update = queue.get()
                # figure out what kind of update is being requested
                if update[0] == CmdProgressBarUpdateTypes.UPDATE_PROGRESS:
                    progress = update[1]
                    last_known_progress = progress
                else:
                    msg = update[1]
                # signal that the value has been consumed
                queue.task_done()

            num_progress_vals = bs(progress_values, progress)
            progress_info = '..'.join([''.join((str(i), '%')) for i in progress_values[:num_progress_vals]])
            progress_info = ''.join((progress_info, '.' * (53 - len(progress_info))))

            # for info msg updates, display the message
            if msg != None:
                sys.stdout.write(''.join(('\r', ' ' * 70, '\r')))
                sys.stdout.write(''.join((msg, '\n')))
                msg = None

            # show pogress
            for c in chars:
                sys.stdout.write('\r[ {0} ..{1}.. ]'.format(c, progress_info))
                sys.stdout.flush()
                time.sleep(0.4)

            if end_event.is_set():
                break

    # starts the worker thread
    def start(self):
        self._bar_thread.start()

    # stops the worker thread
    # handles premature exits (e.g., when the method is called at 70% progress)
    def stop(self):
        # check if a graceful stop is needed
        if self._progress < 100:
            # looks like a premature exit,
            # set progress to max
            self.progress = 100

        # wait till the queue is processed
        self._queue.join()

        # OK to stop now
        self._end_event.set()
        self._bar_thread.join()
        sys.stdout.write(''.join(('\r', ' ' * 70, '\r')))
        sys.stdout.flush()

# Quick Dev Test
if __name__ == '__main__':
    start_from, msg_target, progress_target = 30, 40, 60
    with progress_bar(start_from) as p_bar:
        while True:
            if p_bar.progress == msg_target:
                p_bar.info_msg = 'At {}%, and doing well'.format(msg_target)
            if p_bar.progress == progress_target:
                p_bar.info_msg = 'At {}%, and feel like finishing early'.format(progress_target)
                break
            p_bar.progress += 10
    print('All Done')

