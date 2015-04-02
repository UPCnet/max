# -*- coding: utf-8 -*-
from max.MADObjects import MADDict

import unittest


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

    def test_recursive_update_dict(self):
        """
        """
        from max.rest.utils import RUDict
        from max.models import User

        actor = User()
        actor.fromObject({'username': 'sheldon', 'displayName': 'Sheldon'})

        old_dict = {
            'level1_key': {
                'level2_key': {
                    'level3_key': {},
                    'level3_value': 54
                },
                'level2_value': []
            },
            'actor': {}
        }

        new_dict = {
            'level1_key': {
                'level2_key': {
                    'level3_key': {
                        'new_value': 'new'
                    },
                },
                'level2_key2': {'value': 3}
            },
            'actor': actor
        }

        rdict = RUDict(old_dict)
        rdict.update(new_dict)

        self.assertIsInstance(rdict['actor'], User)
        self.assertEqual(rdict['level1_key']['level2_value'], [])
        self.assertEqual(rdict['level1_key']['level2_key']['level3_value'], 54)
        self.assertEqual(rdict['level1_key']['level2_key']['level3_key']['new_value'], 'new')
        self.assertEqual(rdict['level1_key']['level2_key2']['value'], 3)

        self.assertNotEqual(id(rdict['level1_key']), id(new_dict['level1_key']['level2_key']))
        self.assertNotEqual(id(rdict['level1_key']['level2_key']), id(new_dict['level1_key']['level2_key']))
        self.assertNotEqual(id(rdict['level1_key']['level2_key2']), id(new_dict['level1_key']['level2_key2']))
        self.assertEqual(id(rdict['level1_key']['level2_key']['level3_key']['new_value']), id(new_dict['level1_key']['level2_key']['level3_key']['new_value']))
        self.assertEqual(id(rdict['actor']), id(new_dict['actor']))
