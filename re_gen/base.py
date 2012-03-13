# Copyright (c) 2012
# Licensed under the terms of the MIT license; see LICENSE.txt
"""
Syntactic spice to make regexes more fun to read (and hopefully, more fun to write).
"""

from __future__ import absolute_import
import operator
import itertools
import re

from zope.interface import implementer, Interface, Attribute
from .adapterutil import adapter_for, IObjectSequence, IString

class Creator(object):
    def __init__(self, callable, *args, **keywords):
        self.callable = callable
        self.args = args
        self.keywords = keywords
    def __call__(self, *args, **keywords):
        newargs = args + self.args
        newkeywords = dict(self.keywords)
        newkeywords.update(keywords)
        return self.callable(*newards, **newkeywords)

class Pattern(Interface):
    ismodifier = Attribute("Whether the pattern is a modifier for the preceeding atom")
    atoms = Attribute("the number of atoms this pattern contains")

    def simplified():
        "returns simplified version of the pattern"

    def render():
        "renders the pattern as a string"

    def toplevel():
        "returns version of the pattern suitable for top-level rendering"

    def atomized():
        "returns atomic version of the pattern: pattern.atoms == 1"

    def deatomized():
        "returns non-forced-atomic version of the pattern: pattern.atoms >= 1"


class PatternBase(object):
    ismodifier = False
    @property
    def compiled(self):
        """
        Compiled version of regex - accessing will cause compilation
        """
        try:
            return self._compiled
        except AttributeError:
            self.freeze()
            return self._compiled

    @property
    def rendered(self):
        try:
            return self._rendered
        except AttributeError:
            self.freeze()
            return self._rendered

    @property
    def frozen(self):
        return hasattr(self, "_rendered")
        #herp

    def freeze(self):
        self._rendered = self.toplevel().render()
        self._compiled = re.compile(self._rendered)

    def unfreeze():
        try:
            del self._rendered
        except AttributeError:
            pass
        try:
            del self._compiled
        except AttributeError:
            pass

    def simplified(self):
        """
        return simplified version of self and children.
        should not modify self.
        """
        return self

    @property
    def atoms(self):
        """
        Return count of atoms 
        """
        return 1

    def atomized(self):
        """
        Ensure atomic version of self - wrap in a group if necessary, etc
        returned pattern should return 1 from .atoms()
        should not modify self.
        """
        if self.atoms > 1:
            from .grouping import Group
            return Group(self, capturing=False)
        else:
            return self

    def deatomized(self):
        """
        Return non-atomic version of self, if applicable.
        Should be used when an atomic version is unnecessary.
        should not modify self.
        """
        return self

    def toplevel(self):
        """
        Return version of self suitable for use as the top level of a pattern.
        should not modify self.
        """
        return self.simplified().deatomized()

    def warn(self, message):
        print "herp derp %s" % message

    def __str__(self):
        return self.render()

    def search(self, text):
        return self.compiled.search(text)

    def match(self, text):
        return self.compiled.match(text)
    __contains__ = match

@implementer(Pattern)
class StrPattern(PatternBase):
    def __init__(self, str, ismodifier=False, args=None):
        self.str = str
        self.args = args
        self.ismodifier = ismodifier

    def format(self, **args):
        d = {}
        if self.args:
            d.update(self.args)
        d.update(args)
        return StrPattern(self.str, self.doc, self.ismodifier, d)

    def __repr__(self):
        return ("StrPattern(%r, ismodifier=%r, args=%r)" %
                 (self.str, self.ismodifier, self.args))

    def render(self):
        ret = self.str
        if self.args:
            for key, value in self.args.items():
                if key == "dots":
                    key = "..."
                ret = ret.replace(key, str(value))
        return ret

@implementer(Pattern)
class Literal(PatternBase):
    def __init__(self, str):
        self.str = str

    def __repr__(self):
        return "Literal(%r)" % self.str

    def __eq__(self, other):
        if other is self:
            return True
        elif type(other) == Literal:
            return self.str == other.str
        else:
            return False

    def simplified(self):
        from .repeating import Repeating
        repeat, count = derepeat(self.str)
        return Repeating(Literal(repeat), count=count)._drop_if_unnecessary()

    @property
    def atoms(self):
        return len(self.str)

    def render(self):
        return re.escape(self.str)


def derepeat(sequence):
    length = len(sequence)
    for sublen in range(1, length-1):
        if length % sublen != 0:
            continue
        subcount = length/sublen
        firstsub = sequence[:sublen]
        if firstsub * subcount == sequence:
            return (firstsub, subcount)
    return (sequence, 1)


@adapter_for(IObjectSequence)
@implementer(Pattern)
def groupify_sequence(sequence):
    from .grouping import Group
    result = Group(*sequence, capturing=False, _atomic=False)
    return result.simplified(recursive=False, mergechildren=False)


@adapter_for(IString, Pattern)
@implementer(Pattern)
def patternify_string(string):
    return Literal(string).simplified()
