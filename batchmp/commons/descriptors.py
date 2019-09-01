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
import inspect
from types import MethodType, FunctionType
from weakref import WeakKeyDictionary, WeakMethod


class PropertyDescriptor:
    ''' Base Property Descriptor (Python 3.6+)
    ''' 
    # the python 3.6 initializer:
    def __set_name__(self, owner, name):
        self.name = name    

    def __get__(self, instance, owner):
        if instance is None: 
            return self
        return instance.__dict__.get(self.name, None)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value


class LazyClassPropertyDescriptor(PropertyDescriptor):
    ''' Dynamically loads class property of a given custom type
        Example:
          fs_entry_builder = LazyClassPropertyDescriptor('batchmp.fstools.builders.fsb.FSEntryBuilderBase')
    '''
    def __init__(self, property_type_classpath, initialize = True):
        super().__init__()
        self._pt_cpath = property_type_classpath

    def __get__(self, instance, owner=None):
        value = super().__get__(instance, owner = owner)
        if not value:
            value = self.load_lazy_property_class()
            self.__set__(instance, value)
        return value

    def __set__(self, instance, value):
        classname = value.__name__ if inspect.isclass(value) else value.__class__.__name__
        classpath = '.'.join((value.__module__, classname))
        if classpath == self._pt_cpath:
            super().__set__(instance, value)
        else:
            raise TypeError("Type error: {0} is not {1}".format(classpath, self._pt_cpath))

    # Helpers
    def load_lazy_property_class(self):
        split_path = self._pt_cpath.split('.')
        module_path = '.'.join(split_path[:-1])
        class_name = split_path[-1:][0]
        module = import_module(module_path)
        return getattr(module, class_name)


class LazyInstancePropertyDescriptor(LazyClassPropertyDescriptor):
    ''' Dynamically loads instance property of a given custom type
        Example:
          tag_holder = LazyInstancePropertyDescriptor('batchmp.tags.handlers.tagsholder.TagHolder')
    '''    
    # Helpers
    def load_lazy_property_class(self):
        return super().load_lazy_property_class()()


class LazyFunctionPropertyDescriptor:
    ''' Provides lazy property access on the class level
    '''
    def __init__(self, func):
        self._func = func
    def __get__(self, instance, owner=None):
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


class ClassPropertyDescriptor(PropertyDescriptor):
    ''' A function type property descriptor
    '''
    def __set__(self, instance, value):
        if (value is None) or inspect.isclass(value):
            super().__set__(instance, value)
        else:
            raise TypeError("Not a Class: {}".format(instance.__class__))


class WeakMethodPropertyDescriptor(PropertyDescriptor):
    ''' A bound method type property descriptor
        Uses WeakMethod to prevent reference cycles
    '''
    def __get__(self, instance, owner=None):
        value = super().__get__(instance, owner = owner)
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







# class PropertyDescriptor:
#     ''' Base Property Descriptor
#     '''
#     def __init__(self):
#         self.data = WeakKeyDictionary()
# 
#     def __get__(self, instance, type=None):
#         return self.data.get(instance)
# 
#     def __set__(self, instance, value):
#         self.data[instance] = value
# 
#     def __delete__(self, instance):
#         if self.data.get(instance):
#             del self.data[instance]
# 
#     def __set_name__(self, owner, name):
#         self.name = '_' + name

