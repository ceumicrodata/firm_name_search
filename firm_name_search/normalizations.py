# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals


from unidecode import unidecode
import unicodedata

hun_characters = {bytearray([i]).decode('iso-8859-2') for i in range(256)}
hun_punctuation = {
    c
    for c in hun_characters
    if unicodedata.category(c).startswith('P')
}
translate_remove_hun_punctuation = {ord(c): None for c in hun_punctuation}
translate_space_for_hun_punctuation = {ord(c): ' ' for c in hun_punctuation}


def lower(words):
    return tuple(w.lower() for w in words)


def remove_accents(words):
    return tuple(''.__class__(unidecode(w)) for w in words)


def lower_without_accents(words):
    return lower(remove_accents(words))


def remove_punctuations(words):
    return tuple(w.translate(translate_remove_hun_punctuation) for w in words)


def split_on_punctuations(words):
    w = ' '.join(words)
    return tuple(w.translate(translate_space_for_hun_punctuation).split())


CONSONANTS = 'bcdfghjklmnpqrstvwxyz'
# VOWELS = 'aeiou'


def squash(words):
    ''' words -> squashed word
    '''
    text = ''.join(words).lower()
    return ''.join(sorted(set(c for c in text if c in CONSONANTS)))
