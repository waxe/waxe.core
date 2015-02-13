#!/usr/bin/env python

import unittest
from .. import utils


class TestUtils(unittest.TestCase):

    def test_escape_entities(self):
        res = utils.escape_entities('<aurelien@mydomain.com>')
        self.assertEqual(res, '&lt;aurelien@mydomain.com&gt;')

        res = utils.escape_entities('url=test&param=param1')
        self.assertEqual(res, 'url=test&amp;param=param1')
