# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import parse_firm_name as m


class Test_split_org_organization(unittest.TestCase):

    def assert_org(self, expected_org, text):
        firm_name, parsed_org, rest = m.split_org(text.split())
        self.assertEquals(expected_org, parsed_org)

    def test_otp_nyrt_bp_xix_ddd(self):
        self.assert_org('rt', 'otp nyrt, bp xix ...')

    def test_otp_nyrt(self):
        self.assert_org('rt', 'otp nyrt')

    def test_otp_nyilt_rt(self):
        self.assert_org('rt', 'otp nyilt rt')

    def test_otp_nyilt_rt2(self):
        self.assert_org('rt', 'otp nyílt rt')

    def test_otp_nyilt_mukodesu_reszvenytarsasag(self):
        self.assert_org('rt', 'otp nyilt mukodesu reszvenytarsasag')

    def test_x_reszvenytarsasag(self):
        self.assert_org('rt', 'x reszvenytarsasag')

    def test_x_Re_SZVENYTARSASAG(self):
        self.assert_org('rt', 'x RéSZVENYTARSASAG')

    def test_x_btDOT(self):
        self.assert_org('bt', 'x bt.')

    def test_unknown_missing(self):
        self.assert_org(None, 'unknown missing')

    def test_xy_vegrehajtoi_iroda(self):
        self.assert_org('vegrehajto', 'x y végrehajtói iroda')

    def test_xy_vegrehajto_iroda(self):
        self.assert_org('vegrehajto', 'x y végrehajtó iroda')

    def test_xy_kozjegyzoi_iroda(self):
        self.assert_org('kozjegyzo', 'x y közjegyzői iroda')

    def test_xy_kozjegyzo_iroda(self):
        self.assert_org('kozjegyzo', 'x y közjegyző iroda')

    def test_xy_vizgazdalkodasi_tarsulat(self):
        self.assert_org('vgt', 'x y vízgazdálkodási társulat')

    def test_xy_oktatoi_munkakozosseg(self):
        self.assert_org('omk', 'x y oktatói munkaközösség')

    def test_xy_gazdasagi_munkakozosseg(self):
        self.assert_org('gmk', 'x y gazdasági munkaközösség')

    def test_xy_vallalat(self):
        self.assert_org('vallalat', 'x y vállalat')

    def test_xy_egyeni_ceg(self):
        self.assert_org('kfc', 'x y egyéni ceg')
        self.assert_org('kfc', 'x y korlatolt feleossegu egyéni ceg')
        self.assert_org('kfc', 'x y ec')

    def test_xy_vallalkozas_fioktelepe(self):
        self.assert_org(
            'fioktelep',
            'x y vállalkozas magyarorszagi fioktelepe'
        )


class Test_split_org_firm_name(unittest.TestCase):

    def assert_firm_name(self, expected_firm_name, text):
        parsed_firm_name, org, rest = m.split_org(text.split())
        self.assertEquals(expected_firm_name, parsed_firm_name)

    def test_otp_nyrt_bp_xix_ddd(self):
        self.assert_firm_name(['otp'], 'otp nyrt, bp xix ...')

    def test_otp_nyrt(self):
        self.assert_firm_name(['otp'], 'otp nyrt')

    def test_otp_nyilt_rt(self):
        self.assert_firm_name(['otp'], 'otp nyilt rt')

    def test_unknown_missing(self):
        self.assert_firm_name(['unknown', 'missing'], 'unknown missing')


class Test_split_org_rest(unittest.TestCase):

    def assert_rest(self, expected_rest, text):
        firm_name, org, parsed_rest = m.split_org(text.split())
        self.assertEquals(expected_rest, parsed_rest)

    def test_otp_nyrt_bp_xix_ddd(self):
        self.assert_rest(['bp', 'xix', '...'], 'otp nyrt, bp xix ...')

    def test_otp_nyilt_rt(self):
        self.assert_rest([], 'otp nyilt rt')

    def test_unknown_missing(self):
        self.assert_rest([], 'unknown missing')


class Test_parse(unittest.TestCase):

    def assert_parsed_to(self, text, name, organization):
        self.assertEquals(
            m.ParsedFirmName(
                name,
                organization,
            ),
            m.parse(text)
        )

    def test_otp_bank_nyrt(self):
        self.assert_parsed_to('otp bank nyrt', 'otp bank', 'rt')

    def test_otp_bank_nyiltkoruen_mukodo_rt(self):
        self.assert_parsed_to(
            'otp bank nyíltkörűen működő rt',
            'otp bank', 'rt'
        )

    def test_xy_faipari_kereskedelmi_es_szolgaltato_kft(self):
        self.assert_parsed_to(
            'XY Faipari, Kereskedelmi és Szolgáltató Kft',
            'XY Faipari, Kereskedelmi és Szolgáltató', 'kft'
        )

    def test_xy_faipari__kereskedelmi_es_szolgaltato_kft(self):
        self.assert_parsed_to(
            'XY Faipari-, Kereskedelmi és Szolgáltató Kft',
            'XY Faipari-, Kereskedelmi és Szolgáltató', 'kft'
        )
