# Copyright (c) 2012
# Licensed under the terms of the MIT license; see LICENSE.txt

from .repeating import Repeating
from .grouping import Group
from .base import Pattern

def join(joiner, elements): # needs to be updated for use of zope.interface
    multiplier = 1
    if Repeating.is_repeater(elements) and elements.is_fixed:
        multiplier = elements.count
        elements = elements.pattern

    if Group.is_group(elements) and not elements._atomic:
        elements = elements.simplified().children * multiplier

    result = []

    for i, j in zip(elements, [joiner] * len(elements)):
        result.append(i)
        result.append(j)

    return Pattern(result[:-1]).simplified()
