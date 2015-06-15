# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import names as m


class Test_maybe_valid_name(unittest.TestCase):

    def test_xy(self):
        self.assertTrue(m.maybe_valid_name(' xy '))

    def test_xy_felszamolas_alatt(self):
        self.assertFalse(m.maybe_valid_name('xy felszámolás alatt'))

    def test_xy_felszamolas_alatt_(self):
        self.assertFalse(m.maybe_valid_name('xy "felszámolás alatt" ..'))

    def test_xy_fa(self):
        self.assertFalse(m.maybe_valid_name('xy f.a.'))

    def test_felszamolas_alatt_xy(self):
        self.assertFalse(m.maybe_valid_name('felszámolás alatt xy'))

    def test__felszamolas_alatt_xy(self):
        self.assertFalse(m.maybe_valid_name('.. "felszámolás alatt" xy'))
