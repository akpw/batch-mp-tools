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
         LazyFunctionPropertyDescriptor,
         FunctionPropertyDescriptor,
         WeakMethodPropertyDescriptor,
         BooleanPropertyDescriptor)

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
        from batchmp.tags.handlers.tagsholder import TagHolder
        class AClass:
            tag_holder = LazyTypedPropertyDescriptor('batchmp.tags.handlers.tagsholder.TagHolder')
        a, b = AClass(), AClass()
        test_value = 'A Test Artist'
        a.tag_holder.artist = test_value
        self.assertEqual(a.tag_holder.artist, test_value)

        a.tag_holder.title = 'A Test Title'
        b.tag_holder.title = 'B Test Title'
        self.assertNotEqual(a.tag_holder, b.tag_holder)
        self.assertNotEqual(a.tag_holder.title, b.tag_holder.title)

        with self.assertRaises(TypeError):
            b.tag_holder = AClass()

        b.tag_holder = TagHolder()

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

    def test_WeakMethodPropertyDescriptor(self):
        class AClass:
            wp = WeakMethodPropertyDescriptor()
            def aa(self):
                pass
            @staticmethod
            def aaa():
                pass

        class BClass:
            wp = WeakMethodPropertyDescriptor()
            def bb():
                pass

        a, b = AClass(), BClass()

        a.wp = a.aa
        b.wp = b.bb
        self.assertNotEqual(a.wp, b.wp)

        with self.assertRaises(TypeError):
            a.wp = a.aaa

        r = weakref.ref(a)
        del a
        gc.collect()
        self.assertIsNone(r())

    def test_FunctionPropertyDescriptor(self):
        class AClass:
            fp = FunctionPropertyDescriptor()
            def aa(self):
                pass
            @staticmethod
            def aaa():
                pass

        class BClass:
            fp = FunctionPropertyDescriptor()
            @staticmethod
            def bbb():
                pass

        a, b = AClass(), BClass()

        a.fp = a.aaa
        b.fp = b.bbb
        self.assertNotEqual(a.fp, b.fp)

        with self.assertRaises(TypeError):
            a.fp = a.aa

        r = weakref.ref(a)
        del a
        gc.collect()
        self.assertIsNone(r())

    def test_BooleanPropertyDescriptor(self):
        class AClass:
            bln = BooleanPropertyDescriptor()
        a, b = AClass(), AClass()

        a.bln = True
        b.bln = False
        self.assertNotEqual(a.bln, b.bln)

        with self.assertRaises(TypeError):
            a.bln = 1

        r = weakref.ref(a)
        del a
        gc.collect()
        self.assertIsNone(r())

# quick dev test
if __name__ == '__main__':
    DescriptorTests().test_PropertyDescriptor
    DescriptorTests().test_LazyFunctionPropertyDescriptor()
    DescriptorTests().test_LazyTypedPropertyDescriptor
    DescriptorTests().test_BooleanPropertyDescriptor()
    DescriptorTests().test_FunctionPropertyDescriptor()
    DescriptorTests().test_WeakMethodPropertyDescriptor()



