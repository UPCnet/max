# -*- coding: utf-8 -*-
import unittest

from max.MADObjects import MADDict


class MyMADDict(MADDict):
    schema = {'foo': {}}
    myattribute = 'Hey!'


class FunctionalTests(unittest.TestCase):

    def setUp(self):
        pass

    # BEGIN TESTS

    def test_maddict_assign_non_schema_item(self):
        """
            Test MADDict fails silently on assigning to a key not defined in schema,
            but raises when trying to access that key
        """
        md = MADDict()
        md['foo'] = 'bar'

        def getitem():
            md['foo']

        self.assertRaises(KeyError, getitem)

    def test_maddict_assign_schema_item(self):
        """
            Test MADDict allows to assign a value to a key defined in schema
            and retrieve that value
        """
        md = MyMADDict()
        md['foo'] = 'bar'
        self.assertEqual(md['foo'], 'bar')

    def test_maddict_access_items_as_attributes(self):
        """
            Test MADDict allows to access item keys as attributes
        """
        md = MyMADDict()
        md['foo'] = 'bar'
        self.assertEqual(md.foo, 'bar')

    def test_maddict_assign_items_as_attributes(self):
        """
            Test MADDict saves values on the dict structure
            when accesed as an item key defined on schema property
        """
        md = MyMADDict()
        md.foo = 'bar'
        self.assertEqual(dict.__getitem__(md, 'foo'), 'bar')

    def test_maddict_assign_custom_class_attributes(self):
        """
            Test MADDict saves values on the object attribue
            when accesed as an attribute defined on the class
        """
        md = MyMADDict()
        md.myattribute = 'bar'
        self.assertEqual(object.__getattribute__(md, 'myattribute'), 'bar')

        def getAsIfItWasAnitem():
            dict.__getitem__(md, 'myattribute')
        self.assertRaises(KeyError, getAsIfItWasAnitem)
