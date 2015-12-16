#!/usr/bin/env python

import unittest
import mock
from .. import config_parser


class Class1(object):
    EXTENSIONS = ['.xml']
    ROUTE_PREFIX = 'xml'


class Class2(object):
    EXTENSIONS = ['.txt']
    ROUTE_PREFIX = 'txt'


class Class3(object):
    EXTENSIONS = ['.txt']
    ROUTE_PREFIX = 'txt'


def fake_import_module(name):
    return {
        'Class1': Class1,
        'Class2': Class2,
        'Class3': Class3,
    }[name]


class TestConfigParser(unittest.TestCase):

    def test__parse_waxe_modules(self):
        propname = 'prop'
        settings = {propname: 'Class1\nClass2\n'}
        with mock.patch('importlib.import_module',
                        side_effect=fake_import_module):
            res = config_parser._parse_waxe_modules(settings, propname)
            expected = [(['.xml'], Class1), (['.txt'], Class2)]
            self.assertEqual(res, expected)

        settings = {propname: 'Class1\nClass2#.js,css\n'}
        with mock.patch('importlib.import_module',
                        side_effect=fake_import_module):
            res = config_parser._parse_waxe_modules(settings, propname)
            expected = [(['.xml'], Class1), (['.js', '.css'], Class2)]
            self.assertEqual(res, expected)

        settings = {propname: 'Class1\nClass2\nClass3'}
        with mock.patch('importlib.import_module',
                        side_effect=fake_import_module):
            try:
                config_parser._parse_waxe_modules(settings, propname)
                assert(False)
            except Exception, e:
                self.assertTrue(
                    'An extension is defined in many waxe modules' in str(e))

    def test_parse_waxe_editors(self):
        settings = {}
        res = config_parser.parse_waxe_editors(settings)
        self.assertEqual(res, [])

        settings = {'waxe.editors': 'Class1\nClass2\n'}
        with mock.patch('importlib.import_module',
                        side_effect=fake_import_module):
            res = config_parser.parse_waxe_editors(settings)
            expected = [(['.xml'], Class1), (['.txt'], Class2)]
            self.assertEqual(res, expected)

    def test_parse_waxe_renderers(self):
        settings = {}
        res = config_parser.parse_waxe_renderers(settings)
        self.assertEqual(res, [])

        settings = {'waxe.renderers': 'Class1\nClass2\n'}
        with mock.patch('importlib.import_module',
                        side_effect=fake_import_module):
            res = config_parser.parse_waxe_renderers(settings)
            expected = [(['.xml'], Class1), (['.txt'], Class2)]
            self.assertEqual(res, expected)
