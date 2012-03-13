# Copyright (c) 2012
# Licensed under the terms of the MIT license; see LICENSE.txt

from .base import StrPattern, Pattern, PatternBase, Creator

from zope.interface import implementer, Attribute

zerotoinf_pattern = StrPattern("*", ismodifier=True)
onetoinf_pattern = StrPattern("+", ismodifier=True)
zerotoone_pattern = StrPattern("?", ismodifier=True)
exactlyx_pattern = StrPattern("{m}", ismodifier=True)
xtox_pattern = StrPattern("{m,n}", ismodifier=True)

# this is used separately than zerotoone_pattern
nongreedy_pattern = StrPattern("?", ismodifier=True)

# NOT float('inf'), because that results in a silent error (NaN) when multiplied by 0
# TODO: make this a singleton of a class with a proper __repr__
inf = object()

class IRepeating(Pattern):
    pattern = Attribute("the pattern to be repeated")
    greedy = Attribute("whether the pattern is greedy")
    min = Attribute("Minimum repetitions to match")
    max = Attribute("Maximum repetitions to match")

@implementer(IRepeating)
class Repeating(PatternBase):
    ismodifier = False
    def __init__(self, pattern, count=-1, min=1, max=inf, greedy=True):
        self.child = pattern
        self.greedy = greedy

        if count > -1:
            max = count
            min = count

        self.max = max
        self.min = min

        self.modifier = self.calc(min, max)

    @property
    def is_fixed(self):
        return self.max == self.min

    @property
    def count(self):
        if self.is_fixed:
            return self.min
        else:
            return None

    def calc(self, min, max):
        counts = (min, max)
        if min == inf:
            raise Exception("minimum count cannot be infinite")
        elif max == 0:
            raise Exception("maximum count cannot be 0")
        elif counts == (1, 1):
            return None
        elif counts == (0, inf):
            return zerotoinf_pattern
        elif counts == (1, inf):
            return onetoinf_pattern
        elif counts == (0, 1):
            return zerotoone_pattern
        elif min == self.max:
            return exactlyx_pattern.format(m=self.min)
        else:
            m = "" if min == 0 else min
            n = "" if max == inf else max
            return xtox_pattern.format(m=m, n=n)

    ### ------ Simplification ------

    def _drop_if_unnecessary(self, pattern=None, min=None, max=None):
        if (pattern, min, max) == (None, None, None):
            pattern = self.child
            min = self.min
            max = self.max
            createnew = False
        else:
            createnew = True

        if not self.calc(min, max):
            return pattern.deatomized()
        elif createnew:
            return Repeating(pattern, min=min, max=max, greedy=self.greedy)
        else:
            return self

    def _merge_child(self, pattern=None):
        if pattern == None:
            pattern = self.child
        min = self.min
        max = self.max
        if IRepeating.providedBy(pattern):
            # todo: delegate to child, like how Group does?
            assert self.greedy == pattern.greedy # how the crap do you reconcile greedyness anyway
            subrepeater = pattern
            pattern = subrepeater.pattern
            if inf in (max, subrepeater.max):
                max = inf
            else:
                max *= subrepeater.max
            min *= subrepeater.min
        return pattern, min, max

    def _prerender(self):
        pattern = Pattern(self.child)
        if self.modifier:
            pattern = pattern.atomized()
        return pattern

    def simplified(self, recursive=True):
        pattern = self._prerender()
        if recursive:
            pattern = pattern.simplified()

        pattern, min, max = self._merge_child(pattern)

        return self._drop_if_unnecessary(pattern, min, max)

    ### ------ Rendering ------

    def render(self):
        pattern = self._prerender()
        if self.modifier:
            result = [pattern.atomized().render()]
            result.append(self.modifier.render())
            if not self.greedy:
                result.append(nongreedy_pattern.render())
            return "".join(result)
        else:
            return pattern.render()

    def __repr__(self):
        args = [repr(self.child)]
        if self.min == self.max:
            args.append("count=%r" % self.min)
        else:
            if self.min != 1:
                args.append("min=%r" % self.min)
            if self.max != inf:
                args.append("max=%r" % self.max)
        if not self.greedy:
            args.append("greedy=False")
        return "Repeating(%s)" % ", ".join(args)

optional = Creator(Repeating, min=0, max=1)

#any_of = Creator(Set)
#anything_but = Creator(Set, invert=True)
