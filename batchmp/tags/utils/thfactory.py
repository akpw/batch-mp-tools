# coding=utf8
## Copyright (c) 2014 Arseniy Kuznetsov
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

from batchmp.tags.handlers.ffmphandler import FFmpegTagHandler
from batchmp.tags.handlers.mtghandler import MutagenTagHandler

""" Tag Handlers Factory
"""
class TagHandlerFactory:
    def __init__(self):
        self._handlers = [MutagenTagHandler(), FFmpegTagHandler()]

    def handler(self, mfname):
        ''' Returns suitable handler for a media file
        '''
        for handler in self._handlers:
            if handler.can_handle(mfname):
                return handler

        return None

