# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import argparse
from collections import namedtuple
import difflib
import operator
import os
import petl
from petl.io.sources import FileSource
import sys
import textwrap

from .search import NameToTaxidsIndex, TaxidToNamesIndex
from .parse_firm_name import parse as parse_firm_name


def _get_terminal_width():
    try:
        return int(os.environ['COLUMNS'])
    except (KeyError, ValueError):
        return 80


def _wordwrap(text):
    return textwrap.fill(textwrap.dedent(text), _get_terminal_width() - 2)


def main(argv, version):
    ww = _wordwrap

    description = '\n'.join((
        ww('Add tax_id to input by searching for the firm name'),
        '',
        ww(
            '''\
            NOTE: this program can recreate the index file used
            for searching with
            '''),
        '    %(prog)s index ...',
        ww('(usage details are in its separate --help message)'),
        ))
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description)
    parser.add_argument(
        '--index', default='complex_firms.sqlite',
        help='sqlite file to use as index (default: %(default)s)')
    parser.add_argument(
        'firm_name_field',
        help='firm name field name in input csv')
    parser.add_argument(
        'input_csv', type=FileSource,
        help='input csv file')
    parser.add_argument(
        'output_csv', type=FileSource,
        help='output csv file')
    parser.add_argument(
        '--taxid',
        default='tax_id',
        help='output field for found tax_id (default: %(default)s)')
    parser.add_argument(
        '--text_score',
        default='text_score',
        help=(
            '''output field for found tax_id's text score
            (default: %(default)s)'''))
    parser.add_argument(
        '--org_score',
        default='org_score',
        help=(
            '''output field for found tax_id's organization score
            (default: %(default)s)'''))
    parser.add_argument(
        '--found_name',
        default='found_name',
        help=(
            '''
            output field for the best matching name
            (default: %(default)s)
            '''))
    parser.add_argument(
        '-V', '--version', action='version',
        version='%(prog)s {}'.format(version),
        help='Show version info')
    args = parser.parse_args(argv)

    petl.io.tocsv(_find_firms(args), args.output_csv, encoding='utf-8')


def _find_firms(args):
    input_source = petl.io.fromcsv(args.input_csv, encoding='utf-8')

    input = iter(input_source)
    header = next(input)
    assert args.firm_name_field in header
    assert args.taxid not in header
    assert args.text_score not in header
    assert args.org_score not in header
    assert args.found_name not in header

    get_firm_name = operator.itemgetter(header.index(args.firm_name_field))
    find_complex = FirmFinder(args.index).find_complex

    yield (
        tuple(header) +
        (args.org_score, args.text_score, args.found_name, args.taxid))

    for row in input:
        match = find_complex(get_firm_name(row))
        yield (
            tuple(row) +
            (match.org_score, match.text_score, match.found_name, match.tax_id))


ComplexMatch = namedtuple('ComplexMatch', 'org_score text_score found_name tax_id')
NO_MATCH = ComplexMatch(-20, -20, '', None)
assert NO_MATCH.org_score == -20
assert NO_MATCH.text_score == -20
assert NO_MATCH.found_name == ''
assert NO_MATCH.tax_id is None


class FirmFinder(object):

    def __init__(self, index_location):
        self.taxid_to_names = self._get_taxid_to_names(index_location)
        self.name_to_taxids = self._get_name_to_taxids(index_location)

    def find_complex(self, firm_name):
        score = MatchScorer(firm_name, self.taxid_to_names).score
        tax_ids = self.name_to_taxids(firm_name)
        matches = sorted(score(tax_id) for tax_id in tax_ids)
        return matches.pop() if matches else NO_MATCH

    def _get_taxid_to_names(self, index_location):
        # returns a function
        taxid_to_names = TaxidToNamesIndex(location=index_location)
        taxid_to_names.open()
        return taxid_to_names.find

    def _get_name_to_taxids(self, index_location):
        # returns a function
        name_to_taxids = NameToTaxidsIndex(location=index_location)
        name_to_taxids.open()
        _find = name_to_taxids.find

        def find(name):
            return set(firm_id.tax_id for firm_id in _find(name))
        return find


class MatchScorer(object):

    def __init__(self, name, taxid_to_names):
        self.name = name
        self.parsed = parse_firm_name(name)
        self.taxid_to_names = taxid_to_names

    def score(self, taxid):
        '''
            Find best matching name with taxid.
        '''
        max_name = ComplexMatch(-10, -10, '', taxid)
        for name in self.taxid_to_names(taxid):
            parsed = parse_firm_name(name)
            # org_score
            if self.parsed.organization is None:
                # we *WERE NOT* given an initial organization
                org_score = 1
            elif parsed.organization is None:
                # could not parse the organization
                org_score = 0
            elif self.parsed.organization == parsed.organization:
                org_score = 2
            else:
                # do not match
                org_score = -1
            text_score = self.text_score(self.parsed.name, parsed.name)
            max_name = max(max_name, ComplexMatch(org_score, text_score, name, taxid))
        return max_name

    def text_score(self, text1, text2):
        sm = difflib.SequenceMatcher(a=text1.lower(), b=text2.lower())
        return sm.ratio()


if __name__ == '__main__':
    main(sys.argv[1:], 'test-version')
