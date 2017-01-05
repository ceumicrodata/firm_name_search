# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import argparse
from collections import namedtuple
from glob import glob
import sqlite3
import operator
import os
import petl
import sys

from .db import SqliteConstantMap
from .names import maybe_valid_name
from .index import heads


def single_matching_file(pattern):
    candidates = glob(pattern)
    return candidates[0] if 1 == len(candidates) else None


def error(parser, msg):
    error_msg = 'ERROR: {}\n'.format(msg)
    eye_magnet = '!!!!!  ' + '!' * len(msg) + '\n'
    #
    sys.stderr.write(eye_magnet)
    sys.stderr.write(error_msg)
    sys.stderr.write(eye_magnet)
    sys.stderr.write('\n')
    #
    parser.print_help()
    sys.exit(1)


def verify_inputs(inputs, parser):
    for key in inputs:
        if inputs[key] is None:
            error(
                parser,
                (
                    '{} was not specified and there is' +
                    ' no suitable default available'
                ).format(key), parser)
        if not os.path.exists(inputs[key]):
            error(
                parser,
                '{} for {} is not a readable file'
                .format(inputs[key], key))


def main(argv, version):
    parser = argparse.ArgumentParser(
        description='Create index for mapping between firm names and tax_id')
    parser.add_argument(
        '--target', default='complex_firms.sqlite',
        help='sqlite index file to create (default: %(default)s)')
    parser.add_argument(
        '-0', '--rovat-0-csv', default=single_matching_file('rovat_0.csv*'),
        help='needed for creating the index (default: %(default)s)')
    parser.add_argument(
        '-2', '--rovat-2-csv', default=single_matching_file('rovat_2.csv*'),
        help='needed for creating the index (default: %(default)s)')
    parser.add_argument(
        '-3', '--rovat-3-csv', default=single_matching_file('rovat_3.csv*'),
        help='needed for creating the index (default: %(default)s)')
    args = parser.parse_args(argv)
    inputs = dict(
        rovat_0_csv=args.rovat_0_csv,
        rovat_2_csv=args.rovat_2_csv,
        rovat_3_csv=args.rovat_3_csv)
    verify_inputs(inputs, parser)
    if os.path.exists(args.target):
        error(parser, 'Index file {} already exists'.format(args.target))
    create(index_file_path=args.target, inputs=inputs)


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
        yield Record(
            *(get_simple_attrs(row_dict) + get_calculated_attrs(row_dict)))


def log_to_stderr(msg):
    sys.stderr.write(str(msg) + '\n')


def create(index_file_path, inputs, progress=log_to_stderr):
    progress('Creating index {} ...'.format(index_file_path))
    database = sqlite3.connect(index_file_path)
    # NOTE: database is shared between maps
    name_to_tax_ids = SqliteConstantMap(database, tablename='name_to_tax_ids')
    tax_id_to_names = SqliteConstantMap(database, tablename='tax_id_to_names')

    # build db
    r0_filename = inputs['rovat_0_csv']
    progress('- reading {}'.format(r0_filename))
    cegid_to_taxid = {
        r.ceg_id: r.tax_id
        for r in read_csv(
            r0_filename,
            'ceg_id', tax_id=lambda row: row['adosz'][:8])}

    def populate(input):
        filename = inputs[input]
        progress('- reading {}'.format(filename))

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
        progress('- indexing...')
        name_to_tax_ids.create_index()
        tax_id_to_names.create_index()
    except:
        # remove partial indices
        name_to_tax_ids.drop()
        tax_id_to_names.drop()
        raise
    progress('Index {} successfully created!'.format(index_file_path))


if __name__ == '__main__':
    main(sys.argv[1:], 'test-version')
