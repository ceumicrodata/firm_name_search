# coding: utf-8
from __future__ import unicode_literals

# transliteration from http://www.boutler.de/translit/trans.htm
RUS = (u'\u0430', u'\u0431', u'\u0432', u'\u0433', u'\u0434', u'\u0435', u'\u0451', u'\u0436', u'\u0437',u'\u0438', u'\u0439',
       u'\u043A', u'\u043B', u'\u043C', u'\u043D', u'\u043E', u'\u043F', u'\u0440', u'\u0441', u'\u0442', u'\u0443', u'\u0444',
       u'\u0445', u'\u0446', u'\u0447', u'\u0448', u'\u0449', u'\u044A', u'\u044B', u'\u044C', u'\u044D', u'\u044E', u'\u044F')
HUN = ('a', 'b', 'v', 'g', 'd', 'je', 'jo', 'zs', 'z', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 'sz', 't', 'u', 'f',
       'h', 'c', 'cs', 's', 'scs', '', 'i', '', 'e', 'ju', 'ja')
RUS_HUN = {ord(char): replacement for char, replacement in zip(RUS, HUN)}
RUS_HUN = dict(zip(map(ord, RUS), HUN))

def transliterate_to_hungarian(cyrillic):
    return cyrillic.lower().translate(RUS_HUN)

if __name__ == '__main__':
    print(transliterate_to_hungarian(u'Транслитерация русского алфавита'))
