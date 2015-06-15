# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from abc import ABCMeta, abstractmethod, abstractproperty
import petl
import operator
from collections import namedtuple
import sys

from .db import SqliteConstantMap
from .names import maybe_valid_name
from . import normalizations


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


class FirmId(object):

    def __init__(self, tax_id=None, pir=None):
        self.tax_id = tax_id
        self.pir = pir

    @property
    def as_tuple(self):
        return (self.tax_id, self.pir)

    def __hash__(self):
        return hash(self.as_tuple)

    def __eq__(self, other):
        return self.as_tuple == other.as_tuple

    def __repr__(self):
        if self.pir is None:
            return 'TaxId({0.tax_id})'.format(self)
        if self.tax_id is None:
            return 'PIR({0.pir})'.format(self)
        return (
            '{0.__class__.__name__}(tax_id={0.tax_id}, pir={0.pir})'
        ).format(self)


def log_to_stderr(msg):
    sys.stderr.write(str(msg) + '\n')


class Index(object):

    __metaclass__ = ABCMeta

    def __init__(self, location, inputs, normalize, progress=log_to_stderr):
        self.inputs = inputs
        self.location = location
        self.normalize = normalize
        self.progress = progress
        self.open()

    @abstractproperty
    def exists(self):
        return False

    def open(self):
        '''Ensures that the index is available and usable.'''
        if not self.exists:
            self.create()

        assert self.exists

    @abstractmethod
    def create(self):
        '''Helper for `.open` - populate missing index from inputs'''
        pass

    @abstractmethod
    def find(self, name):
        '''
        -> Matches={score: {FirmId})}
        '''
        raise NotImplementedError


MAX_HEAD_LENGTH = 32


class NameToTaxidsIndex(Index):

    @property
    def exists(self):
        return self.name_to_tax_ids.exists

    def open(self):
        self.name_to_tax_ids = SqliteConstantMap(
            database=self.location, tablename='name_to_tax_ids')
        super(NameToTaxidsIndex, self).open()

    def heads(self, name):
        name_parts = [
            name_part
            for name_part in self.normalize(name).split()
            if name_part
        ]
        for i in range(1, len(name_parts) + 1):
            head = ''.join(name_parts[:i])
            yield head
            if len(head) >= MAX_HEAD_LENGTH:
                break

    def create(self):
        assert not self.exists

        # build db
        self.progress('reading rovat_0.csv')
        cegid_to_taxid = {
            r.ceg_id: r.tax_id
            for r in read_csv(
                self.inputs['rovat_0_csv'],
                'ceg_id', tax_id=lambda row: row['adosz'][:8]
            )
        }

        def populate_name_to_tax_ids(input):
            filename = self.inputs[input]
            self.progress('reading {}'.format(filename))

            heads = self.heads
            for i, r in enumerate(read_csv(filename, 'nev', 'ceg_id'), 1):
                if i % 100000 == 0:
                    self.progress(i)
                tax_id = cegid_to_taxid[r.ceg_id]
                # if tax_id and maybe_valid_name(r.nev):
                if tax_id:
                    for head in heads(r.nev):
                        self.name_to_tax_ids.add(head, tax_id)

        try:
            populate_name_to_tax_ids('rovat_2_csv')
            populate_name_to_tax_ids('rovat_3_csv')
            self.progress('indexing...')
            self.name_to_tax_ids.create_index()
        except:
            # remove partial index
            self.name_to_tax_ids.drop()
            raise
        self.progress('index successfully created!')

    def find(self, name):
        head = ''
        tax_ids = set()
        candidates = set()
        candidate_head = ''
        name_to_tax_ids = self.name_to_tax_ids

        for head in self.heads(name):
            tax_ids = name_to_tax_ids[head]
            overrun = not tax_ids

            if overrun:
                head = candidate_head
                tax_ids = candidates
                break

            unique_match = len(tax_ids) == 1

            if unique_match:
                break

            candidate_head = head
            candidates = tax_ids

        if not tax_ids:
            return []

        if len(tax_ids) > 100:
            # too many - do not bother
            firm_ids = [FirmId('*'), FirmId('TOOMANY'), FirmId('*')]
        else:
            firm_ids = set(FirmId(tax_id=tax_id) for tax_id in tax_ids)
        return firm_ids


class TaxidToNamesIndex(Index):

    @property
    def exists(self):
        return self.tax_id_to_names.exists

    def open(self):
        self.tax_id_to_names = SqliteConstantMap(
            database=self.location, tablename='tax_id_to_names')
        super(TaxidToNamesIndex, self).open()

    def create(self):
        assert not self.exists

        # build db
        self.progress('reading rovat_0.csv')
        cegid_to_taxid = {
            r.ceg_id: r.tax_id
            for r in read_csv(
                self.inputs['rovat_0_csv'],
                'ceg_id', tax_id=lambda row: row['adosz'][:8]
            )
        }

        def populate_tax_id_to_names(input):
            filename = self.inputs[input]
            self.progress('reading {}'.format(filename))

            for i, r in enumerate(read_csv(filename, 'nev', 'ceg_id'), 1):
                if i % 100000 == 0:
                    self.progress(i)
                tax_id = cegid_to_taxid[r.ceg_id]
                if tax_id and maybe_valid_name(r.nev):
                    self.tax_id_to_names.add(tax_id, r.nev)

        try:
            populate_tax_id_to_names('rovat_2_csv')
            populate_tax_id_to_names('rovat_3_csv')
            self.progress('indexing...')
            self.tax_id_to_names.create_index()
        except:
            # remove partial index
            self.tax_id_to_names.drop()
            raise

        self.progress('index successfully created!')

    def find(self, tax_id):
        return set(self.tax_id_to_names[tax_id])


def split_on_quote(name):
    '''A simple normalization

    replace " with a space + lowercase the string
    '''
    return name.replace('"', ' ').lower()


def normalize_hun_firm_name(name):
    return ' '.join(
        normalizations.lower_without_accents(
            normalizations.split_on_punctuations([name])
        )
    )
