# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import argparse
import petl
import sys
import operator
from collections import namedtuple
from .db import SqliteConstantMap
from .names import maybe_valid_name
from .search import heads


def main():
    parser = argparse.ArgumentParser(
        description='Add tax_id to input by searching for the firm name')
    parser.add_argument(
        '--index', default='complex_firms.sqlite',
        help='sqlite file to use as index (default: %(default)s)')
    parser.add_argument(
        '-0', '--rovat-0-csv', default='rovat_0.csv',
        help='needed for creating the index (default: %(default)s)')
    parser.add_argument(
        '-2', '--rovat-2-csv', default='rovat_2.csv',
        help='needed for creating the index (default: %(default)s)')
    parser.add_argument(
        '-3', '--rovat-3-csv', default='rovat_3.csv',
        help='needed for creating the index (default: %(default)s)')
    args = parser.parse_args()
    create(
        index_file_path=args.index,
        inputs=dict(
            rovat_0_csv=args.rovat_0_csv,
            rovat_2_csv=args.rovat_2_csv,
            rovat_3_csv=args.rovat_3_csv))


def read_csv(filename, *attrs, **names_to_extractors):
    if len(attrs) > 1:
        get_simple_attrs = operator.itemgetter(*attrs)
    elif attrs:
        def get_simple_attrs(row):
            return (row[attrs[0]],)
    else:
        def get_simple_attrs(row):
            return ()

    name_extractor_pairs = tuple(names_to_extractors.items())
    Record = namedtuple(  # noqa
        'Record', attrs + tuple(name for name, _ in name_extractor_pairs))

    def get_calculated_attrs(row):
        return tuple(extract(row) for _, extract in name_extractor_pairs)

    csv = iter(petl.io.fromcsv(filename, encoding='utf-8'))
    header = next(csv)
    for row in csv:
        row_dict = dict(zip(header, row))
        yield Record(*(get_simple_attrs(row_dict) + get_calculated_attrs(row_dict)))


def log_to_stderr(msg):
    sys.stderr.write(str(msg) + '\n')


def create(index_file_path, inputs, progress=log_to_stderr):
    name_to_tax_ids = SqliteConstantMap(
        database=index_file_path, tablename='name_to_tax_ids')
    tax_id_to_names = SqliteConstantMap(
        database=index_file_path, tablename='tax_id_to_names')
    # FIXME: this is a hack, they should share the connection directly
    tax_id_to_names.db = name_to_tax_ids.db

    # build db
    progress('reading rovat_0.csv')
    cegid_to_taxid = {
        r.ceg_id: r.tax_id
        for r in read_csv(
            inputs['rovat_0_csv'],
            'ceg_id', tax_id=lambda row: row['adosz'][:8])}

    def populate(input):
        filename = inputs[input]
        progress('reading {}'.format(filename))

        for i, r in enumerate(read_csv(filename, 'nev', 'ceg_id'), 1):
            if i % 100000 == 0:
                progress(i)
            tax_id = cegid_to_taxid[r.ceg_id]
            if tax_id:
                for head in heads(r.nev):
                    name_to_tax_ids.add(head, tax_id)
                if maybe_valid_name(r.nev):
                    tax_id_to_names.add(tax_id, r.nev)

    try:
        populate('rovat_2_csv')
        populate('rovat_3_csv')
        progress('indexing...')
        name_to_tax_ids.create_index()
        tax_id_to_names.create_index()
    except:
        # remove partial indices
        name_to_tax_ids.drop()
        tax_id_to_names.drop()
        raise
    progress('index successfully created!')


if __name__ == '__main__':
    main()
