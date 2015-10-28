# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import fixtures
from testtools import TestCase
from . import search as m

import os
import textwrap


class TempWorkingDir(fixtures.TempDir):

    def setUp(self):
        super(TempWorkingDir, self).setUp()
        orig_cwd = os.getcwd()
        os.chdir(self.path)
        self.addCleanup(os.chdir, orig_cwd)


class RedirectStderr(fixtures.Fixture):

    def setUp(self):
        super(RedirectStderr, self).setUp()
        self.stderr = self.useFixture(fixtures.StringStream(''))
        self.useFixture(fixtures.MonkeyPatch('sys.stderr', self.stderr.stream))


ROVAT_0_CSV = '''\
    ceg_id,alrovat_id,bir,cf,szam,nevalrovat,regi_szh,uj_szh,allapot,cim,fiok,plus,ev,adosz
    0101001194,1,01,01,001194,1,,,6,"1055 Budapest, Markó u. 13-17 ",,,,
    0101001464,1,01,01,001464,1,,,6,"1940 Budapest, Andrássy ut 73-75. ",,,,
    0101001466,1,01,01,001466,1,,,6,,,,,
    0101001469,1,01,01,001469,1,,,6,"Budapest, VIII., Fiumei út 4. ",,,,
    0101001488,1,01,01,001488,4,,,2,"1138 Budapest, Váci út 202. ",,11,,10001459241
    0101001489,1,01,01,001489,3,,,6,"1024 Budapest, Lövőház u. 35. ",,,,10001789201
    0101001591,1,01,01,001591,2,,,6,"1215 Budapest, Duna utca 42.sz. ",,10,,10003475201
    0101001593,1,01,01,001593,1,,,6,"Budapest, VIII., Kerepesi út 17. ",,,,
    0101001594,1,01,01,001594,2,,,6,"1047 Budapest, Táncsics M.u. 1-3. ",,,,
'''
ROVAT_2_CSV = '''\
    ceg_id,alrovat_id,hattol,hatig,nev,labj,valtk,valtv,bkelt,tkelt
    0101001194,1,1988-09-06,1993-01-01,Pénzjegynyomda,,,,,
    0101001464,1,1950-09-15,1993-06-30,Magyar Államvasutak,,,,,
    0101001466,1,1951-02-03,,Budapesti Postaigazgatóság,,,,,
    0101001469,1,1950-12-18,,Magyar Postatakarékpénztár,,,,,
    0101001488,1,1970-01-21,1985-11-04,Magyar Hajó- és Darugyár,,,,,
    0101001488,2,1985-11-04,1994-02-25,GANZ-DANUBIUS Hajó- és Darugyár,,,,,
    0101001488,3,1994-02-25,2013-07-03,"GANZ-DANUBIUS Hajó - és Darugyár "" Végelszámolás alatt """,,,,,
    0101001488,4,2013-07-03,,"GANZ-DANUBIUS Hajó - és Darugyár ""felszámolás alatt""",,2013-07-03,,,
    0101001489,1,1969-02-19,1993-12-08,Ganz Villamossági Művek,,,,,
'''
ROVAT_3_CSV = '''\
    ceg_id,alrovat_id,hattol,hatig,nev,labj,valtk,valtv,bkelt,tkelt
    0101001464,1,1986-08-19,1993-06-30,MÁV.,,,,,
    0101001488,1,1970-01-21,1983-09-19,M.H.D.,,,,,
    0101001488,2,1983-09-19,1994-02-25,GANZ-DANUBIUS,,,,,
    0101001488,3,1994-02-25,2013-07-03,"GANZ - DANUBIUS "" Végelszámolás alatt """,,,,,
    0101001488,4,2013-07-03,,"GANZ - DANUBIUS ""f.a.""",,2013-07-03,,,
'''


class RovatCSVs(fixtures.Fixture):

    def setUp(self):
        super(RovatCSVs, self).setUp()

        def new_csv(filename, content):
            with open(filename, 'wb') as f:
                f.write(textwrap.dedent(content).encode('utf-8'))
        new_csv('rovat_0.csv', ROVAT_0_CSV)
        new_csv('rovat_2.csv', ROVAT_2_CSV)
        new_csv('rovat_3.csv', ROVAT_3_CSV)


class ComplexIndex(fixtures.Fixture):

    def setUp(self):
        super(ComplexIndex, self).setUp()
        with RedirectStderr():
            self.index = m.NameToTaxidsIndex(
                location='complex-firms.sqlite',
                inputs=dict(
                    rovat_0_csv='rovat_0.csv',
                    rovat_2_csv='rovat_2.csv',
                    rovat_3_csv='rovat_3.csv',
                ),
                normalize=m.split_on_quote,
            )


class TestNameToTaxidsIndex(TestCase):

    def test_create_new_index(self):
        self.given_complex_rovat_csvs_as_files()
        self.when_an_index_is_created_for_the_first_time()
        self.then_index_file_is_created()

    def test_search_with_existing_index(self):
        self.given_a_newly_created_index()
        self.when_opening_the_index()
        self.then_firms_can_be_found()

    # implementation

    def given_complex_rovat_csvs_as_files(self):
        self.useFixture(TempWorkingDir())
        self.useFixture(RovatCSVs())

    def silently_create_index(self):
        with RedirectStderr():
            self.index = m.NameToTaxidsIndex(
                location='complex-firms.sqlite',
                inputs=dict(
                    rovat_0_csv='rovat_0.csv',
                    rovat_2_csv='rovat_2.csv',
                    rovat_3_csv='rovat_3.csv',
                ),
                normalize=m.split_on_quote,
            )

    when_an_index_is_created_for_the_first_time = silently_create_index

    def then_index_file_is_created(self):
        self.assertTrue(os.path.exists('complex-firms.sqlite'))

    def given_a_newly_created_index(self):
        self.given_complex_rovat_csvs_as_files()
        self.silently_create_index()

    def when_opening_the_index(self):
        self.index = m.NameToTaxidsIndex(
            location='complex-firms.sqlite',
            inputs={},
            normalize=m.split_on_quote,
        )

    def then_firms_can_be_found(self):
        tax_ids = self.index.find('Ganz')
        self.assertEqual(
            set([m.FirmId(tax_id='10001789'), m.FirmId(tax_id='10001459')]),
            tax_ids
        )

        tax_ids = self.index.find('Ganz Villamossági Művek')
        self.assertEqual(set([m.FirmId(tax_id='10001789')]), tax_ids)


class TestTaxidToNamesIndex(TestCase):

    def test_create_new_index(self):
        self.given_complex_rovat_csvs_as_files()
        self.when_an_index_is_created_for_the_first_time()
        self.then_index_file_is_created()

    def test_search_with_existing_index(self):
        self.given_a_newly_created_index()
        self.when_opening_the_index()
        self.then_taxids_can_be_found()

    # implementation

    def given_complex_rovat_csvs_as_files(self):
        self.useFixture(TempWorkingDir())
        self.useFixture(RovatCSVs())

    def silently_create_index(self):
        with RedirectStderr():
            self.index = m.TaxidToNamesIndex(
                location='complex-firms.sqlite',
                inputs=dict(
                    rovat_0_csv='rovat_0.csv',
                    rovat_2_csv='rovat_2.csv',
                    rovat_3_csv='rovat_3.csv',
                ),
                normalize=m.split_on_quote,
            )

    when_an_index_is_created_for_the_first_time = silently_create_index

    def then_index_file_is_created(self):
        self.assertTrue(os.path.exists('complex-firms.sqlite'))

    def given_a_newly_created_index(self):
        self.given_complex_rovat_csvs_as_files()
        self.silently_create_index()

    def when_opening_the_index(self):
        self.index = m.TaxidToNamesIndex(
            location='complex-firms.sqlite',
            inputs={},
            normalize=m.split_on_quote,
        )

    def then_taxids_can_be_found(self):
        self.assertEqual(
            set(['Ganz Villamossági Művek']),
            self.index.find('10001789')
        )

        self.assertEqual(
            set([
                'GANZ-DANUBIUS',
                'GANZ-DANUBIUS Hajó- és Darugyár',
                'M.H.D.',
                'Magyar Hajó- és Darugyár'
            ]),
            self.index.find('10001459')
        )


class Test_FirmId(TestCase):  # noqa

    def test_equality(self):
        self.assertEqual(
            m.FirmId(tax_id='tax_id'),
            m.FirmId(tax_id='tax_id', pir=None)
        )

        self.assertNotEqual(
            m.FirmId(tax_id='tax_id'),
            m.FirmId(tax_id='tax_id', pir='None')
        )

        self.assertEqual(
            m.FirmId(pir='pir'),
            m.FirmId(pir='pir', tax_id=None)
        )

        self.assertNotEqual(
            m.FirmId(pir='pir'),
            m.FirmId(pir='pir', tax_id='None')
        )

    def test_repr(self):
        self.assertEqual('PIR(1)', repr(m.FirmId(pir='1')))
        self.assertEqual('TaxId(1)', repr(m.FirmId(tax_id='1')))
        self.assertEqual(
            'FirmId(tax_id=1, pir=2)', repr(m.FirmId(tax_id='1', pir='2')))
