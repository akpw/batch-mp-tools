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


''' Properties Descriptors Types
'''
from importlib import import_module
from types import MethodType, FunctionType
from weakref import WeakKeyDictionary, WeakMethod


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
    ''' Dynamically instantiates property of a given custom type
        Example:
          tag_holder = LazyTypedPropertyDescriptor('batchmp.tags.handlers.tagsholder.TagHolder')
    '''
    def __init__(self, property_type_classpath):
        super().__init__()
        self._pt_cpath = property_type_classpath

    def __get__(self, instance, type=None):
        value = super().__get__(instance, type = type)
        if not value:
            value = self.__load_lazy_property_class()
            self.__set__(instance, value)
        return value

    def __set__(self, instance, value):
        classpath = '.'.join((value.__module__, value.__class__.__name__))
        if classpath == self._pt_cpath:
            super().__set__(instance, value)
        else:
            raise TypeError("Type error: {0} is not {1}".format(classpath, self._pt_cpath))

    # Helpers
    def __load_lazy_property_class(self):
        split_path = self._pt_cpath.split('.')
        module_path = '.'.join(split_path[:-1])
        class_name = split_path[-1:][0]
        module = import_module(module_path)
        return getattr(module, class_name)()


class LazyFunctionPropertyDescriptor:
    ''' Provides lazy property access on the class level
    '''
    def __init__(self, func):
        self._func = func
    def __get__(self, instance, type=None):
        if instance is None:
            return self
        # this method will only be called when
        # the property has not yet been set on the instance level
        # so checking the instance dictionary here is mostly for the sake of good manners...
        value = instance.__dict__.get(self._func.__name__)
        if not value:
            # the property has not been set yet
            # calculate the value and store it on the instance
            value = self._func(instance)
            instance.__dict__[self._func.__name__] = value
        return value


class FunctionPropertyDescriptor(PropertyDescriptor):
    ''' A function type property descriptor
    '''
    def __set__(self, instance, value):
        if (value is None) or isinstance(value, FunctionType):
            super().__set__(instance, value)
        else:
            raise TypeError("Not a Function Type: {}".format(value))


class WeakMethodPropertyDescriptor(PropertyDescriptor):
    ''' A bound method type property descriptor
        Uses WeakMethod to prevent reference cycles
    '''
    def __get__(self, instance, type=None):
        value = super().__get__(instance, type = type)
        if value:
            return value()
        else:
            return None

    def __set__(self, instance, value):
        if isinstance(value, MethodType):
            super().__set__(instance, WeakMethod(value))
        else:
            raise TypeError("Not a Method Type: {}".format(value))


class BooleanPropertyDescriptor(PropertyDescriptor):
    ''' A boolean type property descriptor
    '''
    def __set__(self, instance, value):
        if isinstance(value, bool):
            super().__set__(instance, value)
        else:
            raise TypeError("Not a Boolean Type: {}".format(value))







