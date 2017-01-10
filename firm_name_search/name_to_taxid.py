# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import argparse
from collections import namedtuple
import difflib
import itertools
import operator
import os
import petl
from petl.io.sources import FileSource
import sys
import textwrap

from .index import NameToTaxidsIndex, TaxidToNamesIndex
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
        ww('Add firm_id to input by searching for the firm name'),
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
        '-x', '--extramatches', default=0, action='count',
        help='''output multiple matches, specify multiple times to increment''')
    parser.add_argument(
        '--firm_id', dest='firm_id',
        default='firm_id',
        help='output field for found firm_id (default: %(default)s)')
    parser.add_argument(
        '--text_score',
        default='text_score',
        help=(
            '''output field for found firm_id's text score
            (default: %(default)s)'''))
    parser.add_argument(
        '--org_score',
        default='org_score',
        help=(
            '''output field for found firm_id's organization score
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

    match_fields = Match(args.org_score, args.text_score, args.found_name, args.firm_id)
    #
    csv_input = iter(petl.io.fromcsv(args.input_csv, encoding='utf-8'))
    output = add_complex_matches(
        csv_input, FirmFinder(args.index), args.firm_name_field, match_fields, args.extramatches)

    try:
        petl.io.tocsv(output, args.output_csv, encoding='utf-8')
    except InvalidParameterError as e:
        sys.stderr.write('ERROR: ')
        sys.stderr.write(str(e))
        sys.stderr.write('\n')
        return 1


Match = namedtuple(
    'Match',
    'org_score text_score found_name firm_id')
NO_MATCH = Match(-20, -20, '', None)
assert NO_MATCH.org_score == -20
assert NO_MATCH.text_score == -20
assert NO_MATCH.found_name == ''
assert NO_MATCH.firm_id is None


def add_complex_matches(csv_input, firm_finder, firm_name_field, match_fields, extramatches):
    '''
        Generate CSV compatible output by extending input with resolved firms
    '''
    def _name(base, i):
        return '{}_{}'.format(base, i) if i else base

    output_fields = [_name(f, i) for i in range(extramatches + 1) for f in match_fields]

    def _output_row(row, matches):
        output = tuple(row)
        for i, match in enumerate(itertools.chain(matches, itertools.repeat(NO_MATCH, 1 + extramatches))):
            output += match
            if i == extramatches:
                return output

    header = next(csv_input)

    if firm_name_field not in header:
        raise FirmNameFieldNotFoundError(firm_name_field, header)
    if set(output_fields).intersection(set(header)):
        raise OverlappingFieldNamesError(output_fields, header)

    _firm_name = operator.itemgetter(header.index(firm_name_field))
    _find_complex = firm_finder.find_complex

    yield list(header) + output_fields
    for row in csv_input:
        yield _output_row(row, _find_complex(_firm_name(row)))


class InvalidParameterError(StandardError):
    pass


class FirmNameFieldNotFoundError(InvalidParameterError):

    def __init__(self, firm_name_field, header):
        self.firm_name_field = firm_name_field
        self.header = header

    def __str__(self):
        return (
            'Firm name field {} was not found in input {}'
            .format(repr(self.firm_name_field), tuple(self.header)))


class OverlappingFieldNamesError(InvalidParameterError):

    def __init__(self, new_fields, header):
        self.new_fields = new_fields
        self.header = header

    def __str__(self):
        overlap = set(self.new_fields).intersection(set(self.header))
        if len(overlap) == 1:
            return (
                'Column {} is already defined {}'
                .format(repr(overlap.pop()), tuple(self.header)))
        return (
            'Columns {} are already defined {}'
            .format(
                ', '.join(repr(name) for name in sorted(overlap)),
                tuple(self.header)))


class FirmFinder(object):

    def __init__(self, index_location):
        self.get_names = self._get_taxid_to_names(index_location)
        self.get_firm_ids = self._get_name_to_taxids(index_location)

    def find_complex(self, firm_name):
        '''
            Translate firm_name to list of possible matches ordered by scores.
        '''
        score = MatchScorer(firm_name, self.get_names).score
        firm_ids = self.get_firm_ids(firm_name)
        matches = sorted((score(firm_id) for firm_id in firm_ids), reverse=True)
        return matches

    def _get_taxid_to_names(self, index_location):
        # returns a function
        index = TaxidToNamesIndex(index_location)
        index.open()
        return index.find

    def _get_name_to_taxids(self, index_location):
        # returns a function
        index = NameToTaxidsIndex(index_location)
        index.open()
        _find = index.find

        def find(name):
            return set(match.firm_id for match in _find(name))
        return find


class MatchScorer(object):

    def __init__(self, name, get_names):
        self.name = name
        self.parsed = parse_firm_name(name)
        self.get_names = get_names

    def score(self, firm_id):
        '''
            Find best matching name with firm_id.
        '''
        max_name = Match(-10, -10, '', firm_id)
        for name in self.get_names(firm_id):
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
            max_name = max(
                max_name,
                Match(org_score, text_score, name, firm_id))
        return max_name

    def text_score(self, text1, text2):
        sm = difflib.SequenceMatcher(a=text1.lower(), b=text2.lower())
        return sm.ratio()


if __name__ == '__main__':
    main(sys.argv[1:], 'test-version')
