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
    ''' Base Property Descriptor
    '''
    def __init__(self):
        self.data = WeakKeyDictionary()

    def __get__(self, instance, type=None):
        return self.data.get(instance)

    def __set__(self, instance, value):
        self.data[instance] = value

    def __delete__(self, instance):
        if self.data.get(instance):
            del self.data[instance]

class LazyTypedPropertyDescriptor(PropertyDescriptor):
    ''' Dynamically instantiates property of a given type
        Example:
          tag_holder = LazyTypedPropertyDescriptor('batchmp.tags.handlers.tagsholder.TagHolder')
    '''
    def __init__(self, property_type_classpath):
        super().__init__()
        self._pt_cpath = property_type_classpath

    def __get__(self, instance, type=None):
        value = self.data.get(instance)
        if not value:
            value = self.__load_lazy_property_class()
            self.data[instance] = value
        return value

    # Helpers
    def __load_lazy_property_class(self):
        split_path = self._pt_cpath.split('.')
        module_path = '.'.join(split_path[:-1])
        class_name = split_path[-1:][0]
        module = import_module(module_path)
        return getattr(module, class_name)()


class LazyFunctionPropertyDescriptor:
    def __init__(self, func):
        self._func = func
    def __get__(self, instance, type=None):
        if instance is None:
            return self
        # this method should only be called when
        # the property has not yet been set on the instance level
        # so checking the instance dictionary here is probably a bit superfluous...
        value = instance.__dict__.get(self._func.__name__)
        if not value:
            # the property has not been set yet
            # calculate the value and store it on the instance
            value = self._func(instance)
            instance.__dict__[self._func.__name__] = value
        return value

