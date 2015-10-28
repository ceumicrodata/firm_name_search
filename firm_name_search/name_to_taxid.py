# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import argparse
import difflib
import operator
import sys
import petl
from petl.io.sources import FileSource, StdinSource, StdoutSource

from .search import NameToTaxidsIndex, TaxidToNamesIndex
from .search import normalize_hun_firm_name
from .parse_firm_name import parse as parse_firm_name


def text_score(text1, text2):
    text1 = text1.lower()
    text2 = text2.lower()
    sm = difflib.SequenceMatcher(a=text1, b=text2)
    return sm.ratio()


class Scorer(object):

    def __init__(self, name, taxid_to_names):
        self.name = name
        self.parsed = parse_firm_name(name)
        self.taxid_to_names = taxid_to_names

    def score(self, taxid):
        max_name = ((-10, -10), '')
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
            score = org_score, text_score(self.parsed.name, parsed.name)
            max_name = max(max_name, (score, name))
        return max_name


def main():
    parser = argparse.ArgumentParser(
        description='Add tax_id to input by searching for the firm name')
    parser.add_argument(
        '--index', default='complex_firms.sqlite',
        help='sqlite file to use as index (default: %(default)s)')
    parser.add_argument(
        'firm_name_field',
        help='firm name field name in input csv')
    parser.add_argument(
        'input', type=FileSource,
        # default=StdinSource(),
        help='input file')
    parser.add_argument(
        'output', type=FileSource,
        # default=StdoutSource(),
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
            '''output field for the best matching name (default: %(default)s)'''))
    parser.add_argument(
        '--rovat-0-csv', default='rovat_0.csv',
        help='needed for creating the index (default: %(default)s)')
    parser.add_argument(
        '--rovat-2-csv', default='rovat_2.csv',
        help='needed for creating the index (default: %(default)s)')
    parser.add_argument(
        '--rovat-3-csv', default='rovat_3.csv',
        help='needed for creating the index (default: %(default)s)')
    args = parser.parse_args()

    petl.io.tocsv(_find_firms(args), args.output, encoding='utf-8')


def get_taxid_to_names(args):
    taxid_to_names = TaxidToNamesIndex(
        location=args.index,
        inputs=dict(
            rovat_0_csv=args.rovat_0_csv,
            rovat_2_csv=args.rovat_2_csv,
            rovat_3_csv=args.rovat_3_csv),
        normalize=normalize_hun_firm_name,
    ).find

    return taxid_to_names


def get_name_to_taxids(args):
    name_to_taxids = NameToTaxidsIndex(
        location=args.index,
        inputs=dict(
            rovat_0_csv=args.rovat_0_csv,
            rovat_2_csv=args.rovat_2_csv,
            rovat_3_csv=args.rovat_3_csv),
        normalize=normalize_hun_firm_name,
    ).find

    def find(name):
        matches = name_to_taxids(name)
        tax_ids = set(
            firm_id.tax_id
            for firm_id in matches
        )
        return tax_ids
    return find


def _find_firms(args):
    input_source = petl.io.fromcsv(args.input, encoding='utf-8')

    input = iter(input_source)
    header = next(input)
    assert args.firm_name_field in header
    assert args.taxid not in header
    assert args.text_score not in header
    assert args.org_score not in header
    assert args.found_name not in header

    get_firm_name = operator.itemgetter(header.index(args.firm_name_field))

    taxid_to_names = get_taxid_to_names(args)
    name_to_taxids = get_name_to_taxids(args)

    yield (
        tuple(header)
        + (args.org_score, args.text_score, args.found_name, args.taxid))

    for row in input:
        firm_name = get_firm_name(row)
        scorer = Scorer(firm_name, taxid_to_names)
        tax_ids = name_to_taxids(firm_name)
        scored = sorted((scorer.score(tax_id), tax_id) for tax_id in tax_ids)
        if scored:
            ((org_score, text_score), found_name), tax_id = scored.pop()
        else:
            org_score, text_score, found_name = (-20, -20, '')
            tax_id = None

        yield tuple(row) + (org_score, text_score, found_name, tax_id)


if __name__ == '__main__':
    main()
