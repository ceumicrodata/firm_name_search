# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from abc import ABCMeta, abstractmethod, abstractproperty

from .db import SqliteConstantMap
from . import normalizations


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


class MissingIndexError(StandardError):
    pass


class Index(object):

    __metaclass__ = ABCMeta

    def __init__(self, location):
        self.location = location

    @abstractproperty
    def exists(self):
        return False

    def open(self):
        '''Ensures that the index is available and usable.'''
        if not self.exists:
            raise MissingIndexError(self.location)

    @abstractmethod
    def find(self, name):
        '''
        -> Matches={score: {FirmId})}
        '''
        raise NotImplementedError


def normalize_hun_firm_name(name):
    return ' '.join(
        normalizations.lower_without_accents(
            normalizations.split_on_punctuations([name])))


MAX_HEAD_LENGTH = 32


def heads(name):
    name_parts = [
        name_part
        for name_part in normalize_hun_firm_name(name).split()
        if name_part]
    for i in range(1, len(name_parts) + 1):
        head = ''.join(name_parts[:i])
        yield head
        if len(head) >= MAX_HEAD_LENGTH:
            break


class NameToTaxidsIndex(Index):

    @property
    def exists(self):
        return self.name_to_tax_ids.exists

    def open(self):
        self.name_to_tax_ids = SqliteConstantMap(
            database=self.location, tablename='name_to_tax_ids')
        super(NameToTaxidsIndex, self).open()

    def find(self, name):
        head = ''
        tax_ids = set()
        candidates = set()
        candidate_head = ''
        name_to_tax_ids = self.name_to_tax_ids

        for head in heads(name):
            tax_ids = name_to_tax_ids[head]

            if tax_ids:
                unique_match = len(tax_ids) == 1

                if unique_match:
                    break

                candidate_head = head
                candidates = tax_ids

        if not tax_ids and candidates:
            head = candidate_head
            tax_ids = candidates

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

    def find(self, tax_id):
        return set(self.tax_id_to_names[tax_id])
