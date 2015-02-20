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

""" Properties Descriptor Types
"""

from weakref import WeakKeyDictionary
from importlib import import_module

class PropertyDescriptor:
    def __init__(self):
        self.data = WeakKeyDictionary()
    def __get__(self, instance, type=None):
        return self.data.get(instance)
    def __set__(self, instance, value):
        self.data[instance] = value

class LazyClassPropertyDescriptor:
    _default_value = object()
    def __init__(self, property_classpath):
        self.data = WeakKeyDictionary()
        self._pclass_path = property_classpath

    def __get__(self, instance, type=None):
        value = self.data.get(instance, self._default_value)
        if value is self._default_value:
            value = self.__load_lazy_property_class()
            self.data[instance] = value
        return value

    def __load_lazy_property_class(self):
        split_path = self._pclass_path.split('.')
        module_path = '.'.join(split_path[:-1])
        class_name = split_path[-1:][0]
        module = import_module(module_path)
        return getattr(module, class_name)()

class LazyFunctionPropertyDescriptor:
    _default_value = object()
    def __init__(self, func):
        self._func = func
    def __get__(self, obj, type=None):
        if obj is None:
            return self
        # this method should only be called when
        # the property has not yet been set on the instance level
        # so checking the instance dictionary here is probably a bit superfluous...
        value = obj.__dict__.get(self._func.__name__, self._default_value)
        if value is self._default_value:
            # the property has not been set yet
            # calculate the value and store it on the instance level
            value = self._func(obj)
            obj.__dict__[self._func.__name__] = value
        return value

