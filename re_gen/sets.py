# Copyright (c) 2012
# Licensed under the terms of the MIT license; see LICENSE.txt

from .base import PatternBase, StrPattern, Creator
from zope.interface import Interface, implementer
from .adapterutil import adapter_for, IObjectSequence

class Set(PatternBase):
    def __init__(self, *args, **keywords):
        self.elements = [SetElement(arg) for arg in args]

        self.invert = keywords.get("invert", False)

    def render(self):
        result = "["
        if self.invert:
            result += "^"
        for element in self.elements:
            result += element.render()
        result += "]"
        return result

not_in = Creator(Set, invert=True)
not_in_ = not_in
in_ = Creator(Set)

class SetElement(Interface):
    def render():
        "render the element as a string"


@adapter_for(str)
@implementer(SetElement)
class _SetChars(object):
    def __init__(self, string):
        self.string = string

    def render(self):
        return "".join(self.escape(c) for c in self.string)

    def escape(self, c):
        if c in ("-", "]", "\\", "^"):
            c = "\\" + c
        return c

@implementer(SetElement)
class Range(_SetChars):
    def __init__(self, min, max):
        self.min = min
        self.max = max
        assert len(min) == 1
        assert len(max) == 1

    def render(self):
        return "%s-%s" % (self.escape(self.min), self.escape(self.max))

@adapter_for(IObjectSequence)
@implementer(SetElement)
def _make_range(sequence):
    return Range(sequence[0], sequence[1])

@implementer(SetElement)
class CharacterClass(StrPattern):
    pass