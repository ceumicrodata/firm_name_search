# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import normalizations as m


class Test_lower(unittest.TestCase):

    def test_arvizturo_tukorfurogep(self):
        self.assertEquals(
            ('árvíztűrő', 'tükörfúrógép'),
            m.lower(['árvíztűrő', 'tükörfúrógép'])
        )
        self.assertEquals(
            ('árvíztűrő', 'tükörfúrógép'),
            m.lower(['ÁRVÍZTŰRŐ', 'TÜKÖRFÚRÓGÉP'])
        )


class Test_remove_accents(unittest.TestCase):

    def test_arvizturo_tukorfurogep(self):
        self.assertEquals(
            ('arvizturo', 'tukorfurogep'),
            m.remove_accents(['árvíztűrő', 'tükörfúrógép'])
        )
        self.assertEquals(
            ('ARVIZTURO', 'TUKORFUROGEP'),
            m.remove_accents(['ÁRVÍZTŰRŐ', 'TÜKÖRFÚRÓGÉP'])
        )


class Test_lower_without_accents(unittest.TestCase):

    def test_arvizturo_tukorfurogep(self):
        self.assertEquals(
            ('arvizturo', 'tukorfurogep'),
            m.lower_without_accents(['árvíztűrő', 'tükörfúrógép'])
        )
        self.assertEquals(
            ('arvizturo', 'tukorfurogep'),
            m.lower_without_accents(['ÁRVÍZTŰRŐ', 'TÜKÖRFÚRÓGÉP'])
        )


class Test_remove_punctuations(unittest.TestCase):

    def test_x_rtDOT(self):
        self.assertEquals(('x', 'rt'), m.remove_punctuations(['x', 'rt.']))


class Test_split_on_punctuations(unittest.TestCase):

    def test_xDOTyDOT_rtDOT_DOT(self):
        self.assertEquals(
            ('x', 'y', 'rt'),
            m.split_on_punctuations(['x.y.', 'rt.', '.'])
        )


class Test_squash(unittest.TestCase):

    def test_abrakadabra(self):
        self.assertEquals(
            'bdkr',
            m.squash(['abrakadabra'])
        )

    def test_ABRAKADABRA(self):
        self.assertEquals(
            'bdkr',
            m.squash(['ABRAKADABRA'])
        )
