# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import re


BAD_NAME_PATTERNS = tuple(
    (re.compile(pattern), pattern)
    for pattern in (
        ".*((fel|végel)számolás|eljárás) alatt.{,5}$",
        "^.{,5}((fel|végel)számolás|eljárás) alatt.*$",
        ".*[fv] ?[.][ ]?a ?[.].{,5}$",  # f.a. v.a.
    )
)


def maybe_valid_name(firm_name):
    firm_name_lower = firm_name.lower()
    for (pattern, name) in BAD_NAME_PATTERNS:
        if pattern.match(firm_name_lower):
            return False
    return True
