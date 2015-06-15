# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

# http://player.hu/biznisz/cegnevvalasztasi-szempontok/
# parse firm name:
#    name, activity, organization type

import collections
import itertools

import normalizations


_ParsedFirmName = collections.namedtuple(
    'ParsedFirmName',
    [
        'name',
        'organization',
    ]
)


class ParsedFirmName (_ParsedFirmName):
    pass


def make_organization():
    # cegformak:
    # https://occsz.e-cegjegyzek.hu/info/page/adm/adm_Help_ReadHelpFile?adm_file=hu/IMOnline/Utmutatok/RovatokCegformahoz.html
    def u(text):
        return ''.__class__(text)

    def T(text):
        return (tuple(text.split()), )

    def _P(iterables):
        if len(iterables) == 1:
            for row in iterables[0]:
                yield row
        else:
            rows1 = _P(iterables[:-1])
            rows2 = iterables[-1]
            for row1 in rows1:
                for row2 in rows2:
                    yield row1 + row2

    def P(*iterables):
        return tuple(_P(iterables))

    def either(*iterables):
        return tuple(itertools.chain(*iterables))

    _RT_TYPE = either(
        P(
            T('nyíltkörűen') + T('zártkörűen'),
            T('működő')
        ),
        P(
            T('nyílt körűen') + T('zárt körűen'),
            T('működő')
        ),
        P(
            T('nyílt') + T('zárt'),
            T('működésű')
        ),
        T('nyílt') + T('zárt') + T('európai'),
    )

    _RT_ORG = T('részvénytársaság') + T('rt')
    _RT = either(
        P(_RT_TYPE, _RT_ORG),
        _RT_ORG + T('nyrt') + T('zrt')
    )

    _KFT = T('korlátolt felelősségű társaság') + T('kft')
    _BT = T('betéti társaság') + T('bt')
    _KHT = T('közhasznú társaság') + T('kht')
    _KKT = T('közkereseti társaság') + T('kkt')
    _VEGREHAJTO = T('végrehajtó iroda') + T('végrehajtói iroda') + T('vh iroda')
    _KOZJEGYZO = T('közjegyző iroda') + T('közjegyzői iroda')
    _VGT = T('vízgazdálkodási társulat') + T('vgt')

    _OMK = T('oktatói munkaközösség') + T('omk') + T('om')
    _GMK = T('gazdasági munkaközösség') + T('gmk') + T('gm')
    # + T('munkaközösség') + T('mk')

    _KFC = T('korlátolt felelősségű egyéni cég') + T('kfc') + T('egyéni cég') + T('ec')
    _VALLALAT = T('vállalat') + T('közös vállalat')
    _SZOVETKEZET = T('szövetkezet') + T('kisszövetkezet')
    _EGYESULES = T('egyesülés') + T('egyesülése')
    _KEPVISELET = P(
        T('külföldiek magyarországi közvetlen kereskedelmi')
        + T('magyarországi közvetlen kereskedelmi')
        + T('közvetlen kereskedelmi'),
        T('képviselete') + T('képviselet')
    )
    _FIOKTELEP = P(
        T('külföldi székhelyű vállalkozás magyarországi')
        + T('külföldi vállalkozás magyarországi')
        + T('vállalkozás magyarországi')
        + T('magyarországi'),
        T('fióktelepe') + T('fióktelep')
    )
    _EGE = T('európai gazdasági egyesülés') + T('ege')
    _SCE = (
        T('korlátolt felelősségű európai szövetkezet sce')
        + T('korlátolt felelősségű európai szövetkezet')
        + T('európai szövetkezet sce')
        + T('európai szövetkezet')
        + T('sce')
    )

    organizations = {}
    for org, org_names in (
        ('rt', _RT),
        ('kft', _KFT),
        ('bt', _BT),
        ('kht', _KHT),
        ('kkt', _KKT),
        ('vgt', _VGT),
        ('omk', _OMK),
        ('gmk', _GMK),
        ('kfc', _KFC),
        ('vegrehajto', _VEGREHAJTO),
        ('kozjegyzo', _KOZJEGYZO),
        ('vallalat', _VALLALAT),
        ('szovetkezet', _SZOVETKEZET),
        ('egyesules', _EGYESULES),
        ('kepviselet', _KEPVISELET),
        ('fioktelep', _FIOKTELEP),
        ('ege', _EGE),
        ('sce', _SCE),
    ):
        for normalize in (
            normalizations.lower,
            normalizations.lower_without_accents
        ):
            organizations.update(
                {
                    normalize(org_name): org
                    for org_name in org_names
                }
            )
    return organizations

# raw organization name -> normalized organization name
ORGANIZATIONS = make_organization()

MAX_ORG_LEN = max(len(raw) for raw in ORGANIZATIONS)


def split_org(words):
    '''
    words -> (firm_name, org, rest)

    Where
    firm_name: list of words before organization type,
               it is most probably the firm's name and its activity description
    org:       organization type - a string or None if not found
    rest:      list of unparsed words at the end of input, might be an address
    '''
    org = None
    rest = []
    if not words:
        return words, org, rest

    # match from end
    for i in range(MAX_ORG_LEN, 0, -1):
        for normalize in (
            normalizations.lower,
            normalizations.lower_without_accents
        ):
            raw_org = normalize(normalizations.remove_punctuations(words[-i:]))
            if raw_org in ORGANIZATIONS:
                return words[:-i], ORGANIZATIONS[raw_org], rest

    # not found - try removing words form the end
    last = words[-1]
    words = words[:-1]
    firm_name, org, rest = split_org(words)
    if org:
        return firm_name, org, rest + [last]
    else:
        # TODO: attempt a fuzzy match to offset typos with difflib
        return list(words) + [last], org, []


def parse(text):
    '''
    raises ValueError if can not parse text
    '''
    words = text.split()
    name_and_activities, organization, rest = split_org(words)
    return ParsedFirmName(
        name=' '.join(name_and_activities),
        organization=organization
    )
