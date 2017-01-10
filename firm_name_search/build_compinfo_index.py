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
from .index import heads


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


def main(version):
    parser = argparse.ArgumentParser(
        description='Create index for mapping between firm names and tax_id')
    parser.add_argument('compinfo_csv', help='input for creating the index')
    parser.add_argument(
        '--target', default='complex_firms.sqlite',
        help='sqlite index file to create (default: %(default)s)')
    args = parser.parse_args()
    if not os.path.exists(args.compinfo_csv):
        error(parser, '{} is not a readable file'.format(args.compinfo_csv))
    if os.path.exists(args.target):
        error(parser, 'Index file {} already exists'.format(args.target))
    create(args.compinfo_csv, args.target)


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


def create(compinfo_csv, index_file_path, progress=log_to_stderr):
    progress('Creating index {} ...'.format(index_file_path))
    database = sqlite3.connect(index_file_path)
    # FIXME: to reuse the search algorithm, we need to pretend that bvdidnumber-s are tax_id-s
    # NOTE: database is shared between maps
    name_to_tax_ids = SqliteConstantMap(database, tablename='name_to_tax_ids')
    tax_id_to_names = SqliteConstantMap(database, tablename='tax_id_to_names')

    # build db
    try:
        progress('- reading {}'.format(compinfo_csv))
        for i, r in enumerate(read_csv(compinfo_csv, 'companyname', 'bvdidnumber'), 1):
            if i % 100000 == 0:
                progress(i)
            id = r.bvdidnumber
            for head in heads(r.companyname):
                name_to_tax_ids.add(head, id)
            tax_id_to_names.add(id, r.companyname)
        
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
    main('test-version')
