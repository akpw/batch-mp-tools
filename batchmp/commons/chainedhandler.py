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

""" A Chain of Responsibility impl
    Usage:
    >>> handler = ConcreteHandler1() + ConcreteHandler2() + ...
    >>> if handler.can_handle(request):
        .... handler.operation()

    Example:
        batchmp.tags.handlers.basehandler.TagHandler
"""

from abc import ABCMeta, abstractmethod
from batchmp.commons.descriptors import LazyFunctionPropertyDescriptor
from weakref import ref, ReferenceType

class ChainedHandler(metaclass = ABCMeta):
    class HandlersChainDispatcher:
        ''' Internal dispatcher for chained handlers
        '''
        def __init__(self):
            self._handlers_chain = []
            self._responder_idx = -1

        def add_handler(self, handler):
            ''' Adds a handler to the chain
            '''
            if len(self._handlers_chain) == 0:
                # the first handler owns the chain,
                # hence it needs to be added as a weakref
                self._handlers_chain.append(ref(handler))
            else:
                self._handlers_chain.append(handler)

        def has_responder(self, request):
            ''' Evaluates the handler chain and select a suitable responder
            '''
            for idx, handler in enumerate(self._handlers_chain):
                if type(handler) is ReferenceType:
                    handler = handler()
                if handler and handler._can_handle(request):
                    self._responder_idx = idx
                    return True
            return False

        @property
        def responder(self):
            ''' Returns the curent responder
            '''
            if self._responder_idx >= 0:
                handler = self._handlers_chain[self._responder_idx]
                if type(handler) is ReferenceType:
                    handler = handler()
                return handler
            else:
                return None

    @LazyFunctionPropertyDescriptor
    def _handler_chain(self):
        ''' lazily creates the chain dispatcher and
            stores is as an internal property
            via @LazyFunctionPropertyDescriptor
        '''
        handler_chain = ChainedHandler.HandlersChainDispatcher()
        handler_chain.add_handler(self)
        return handler_chain

    @property
    def responder(self):
        ''' Returns active responder
        '''
        return self._handler_chain.responder

    def __add__(self, handler):
        ''' Adds a handler to the handlers chain
        '''
        if not isinstance(handler, ChainedHandler):
            raise TypeError('ChainedHandler.__add__() expects a ChainedHandler instance')
        handler._handler_chain = self._handler_chain
        self._handler_chain.add_handler(handler)

        return self

    def can_handle(self, request):
        return self._handler_chain.has_responder(request)

    # Abstract methods
    @abstractmethod
    def _can_handle(self, request):
        ''' implement in specific handlers
        '''
        return False

