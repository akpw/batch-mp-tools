#!/usr/bin/env python
# coding=utf8
## Copyright (c) 2014 Arseniy Kuznetsov
##
## This propogram is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This propogram is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

import unittest, weakref, gc
from batchmp.commons.descriptors import (
         PropertyDescriptor,
         LazyTypedPropertyDescriptor,
         LazyFunctionPropertyDescriptor)

class DescriptorTests(unittest.TestCase):
    def test_PropertyDescriptor(self):
        class AClass:
            prop = PropertyDescriptor()
        a, b = AClass(), AClass()
        a.prop = 'A Property'
        self.assertEqual(a.prop, 'A Property')

        b.prop = 'B Property'
        self.assertNotEqual(a.prop, b.prop)

        r = weakref.ref(a)
        del a
        gc.collect()
        self.assertIsNone(r())

    def test_LazyTypedPropertyDescriptor(self):
        class AClass:
            prop = LazyTypedPropertyDescriptor('batchmp.tags.handlers.tagsholder.TagHolder')
        a, b = AClass(), AClass()
        test_value = 'A Test Artist'
        a.prop.artist = test_value
        self.assertEqual(a.prop.artist, test_value)

        a.prop.title = 'A Test Title'
        b.prop.title = 'B Test Title'
        self.assertNotEqual(a.prop, b.prop)
        self.assertNotEqual(a.prop.title, b.prop.title)

        r = weakref.ref(a)
        del a
        gc.collect()
        self.assertIsNone(r())

    def test_LazyFunctionPropertyDescriptor(self):
        test_value = 'A Test Value'
        class AClass:
            @LazyFunctionPropertyDescriptor
            def property_method(self):
                return test_value
        a = AClass()
        self.assertEqual(a.property_method, test_value)

        r = weakref.ref(a)
        del a
        gc.collect()
        self.assertIsNone(r())
