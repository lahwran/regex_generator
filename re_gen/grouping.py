# Copyright (c) 2012
# Licensed under the terms of the MIT license; see LICENSE.txt

from .base import StrPattern, Pattern, PatternBase, derepeat
from .repeating import Repeating

from zope.interface import implementer

capturing_pattern = StrPattern("(...)")
noncapturing_pattern = StrPattern("(?:...)")
named_pattern = StrPattern("(?P<name>...)")

class IGroup(Pattern):
    def _merge_nonatomic_child():
        "return simplified version of group for use in parent"

@implementer(IGroup)
class Group(PatternBase):
    def __init__(self, *children, **args):
        self._init(**args)
        self.children = children

    def _init(self, capturing=True, name=None, _atomic=True):
        self.capturing = capturing
        self.name = name
        if name and not capturing:
            raise Exception("Groups cannot be both named and non-capturing")
        elif name:
            # TODO: assert isidentifier(name)
            self.pattern = named_pattern.format(name=name)
        elif capturing:
            self.pattern = capturing_pattern
        else:
            self.pattern = noncapturing_pattern

        if not _atomic: # should not be used by users of the library; is implementation detail
            self.pattern = None
            self.capturing = False
        self._atomic = _atomic

    def copy(self, children=None, **keywords):
        if children == None:
            children = self.children

        args = dict(_atomic=self._atomic, capturing=self.capturing, name=self.name)
        args.update(keywords)
        return Group(*children, **args)

    def atomized(self):
        if not self._atomic:
            return self.copy(_atomic=True)
        else:
            return self

    def deatomized(self, _warn=True):
        if self._atomic:
            if self.capturing and _warn:
                self.warn("de-atomizing a capturing group - capturing-ness will be lost!")
            result = self.copy(_atomic=False)
        else:
            result = self
        return result._drop_if_unnecessary()

    def toplevel(self):
        if self.name and self.capturing:
            self.warn("using a named group as top-level - sub-groups will have numerical indices starting from 2!!")
            return self.simplified()
        elif not self.capturing:
            self.warn("using non-capturing group as top-level - will be captured as "
                        "group 0 anyway due to how the re module numbers groups.")
        return self.deatomized(False).simplified()

    @property
    def ismodifier(self):
        if self._atomic:
            return False
        return len(self.children) and self.children[0].ismodifier

    @property
    def atoms(self):
        if self._atomic:
            return 1
        else:
            return sum(child.atoms for child in self.children)

    ### ------ Simplification ------

    def _merge_nonatomic_child(self):
        if not self._atomic:
            return self.children
        else:
            return [self]

    def _drop_if_unnecessary(self, children=None):
        """
        Return child if group is unnecessary
        """
        if children == None:
            children = self.children

        if (not self.capturing and len(children) == 1 and
            (not self._atomic or self.children[0].atoms <= 1)):
            return children[0]
        else:
            return Group(*children, _atomic=self._atomic, capturing=self.capturing,
                        name=self.name)

    def _derepeat_pre(self, children=None):
        """
        do first part of derepeating - this part must operate on an unmodified
        children list, or it may fail to correctly derepeat
        """
        if children == None:
            children = self.children
        return derepeat(children)

    def _derepeat_post(self, pattern, count):
        """
        finish derepeating by wrapping in Repeating object if necessary
        """
        return Repeating(pattern, count=count)._drop_if_unnecessary()

    def derepeated(self):
        "return derepeated version of self, with no other changes"
        children, count = self._derepeat_pre()

        return self._derepeat_post(self.copy(children=children), count)

    def _merged_children(self, children=None):
        if children == None:
            children = self.children

        newchildren = []
        for child in children:
            if IGroup.providedBy(child):
                newchildren.extend(child._merge_nonatomic_child())
            else:
                newchildren.append(child)
        return newchildren

    def _prerender(self, children=None):
        if children == None:
            children = self.children
        return [Pattern(child) for child in children]

    def simplified(self, recursive=True, mergechildren=True):
        children, count = self._derepeat_pre()
        children = self._prerender(children)
        if recursive:
            children = [child.simplified() for child in children]

        if mergechildren:
            children = self._merged_children(children)

        result = self._drop_if_unnecessary(children)

        return self._derepeat_post(result, count)

    ### ------ Rendering ------

    def render(self):
        result = []
        for child in self.children:
            result.append(Pattern(child).render())
        resultstr = "".join(result)

        if not self._atomic:
            return resultstr
        else:
            return self.pattern.format(dots=resultstr).render()

    def __repr__(self):
        extra = []
        if not self.capturing:
            extra.append("capturing=False")
        if self.name:
            extra.append("name=%r" % self.name)
        if not self._atomic:
            extra.append("_atomic=False")
        return "Group(%s)" % ", ".join([repr(child) for child in self.children] + extra)


@implementer(Pattern)
class PrevGroup(PatternBase):
    earliernamed = StrPattern("(?P=name)")
    earlierid = StrPattern("\\number")
    def __init__(self, name):
        if str(name).isdigit() and int(name):
            self.pattern = self.earlierid.format(number=str(name))
        else:
            self.pattern = self.earliernamed.format(name=name)

    def render(self):
        return self.pattern.render()

@implementer(Pattern)
class Lookahead(PatternBase): # TODO FIXME XXX
    positive = StrPattern("(?=...)")
    negative = StrPattern("(?!...)")
    def _init(self, negative=False):
        if negative:
            self.group = self.negative
        else:
            self.group = self.positive

@implementer(Pattern)
class Lookbehind(Lookahead):
    positive = StrPattern("(?<=...)")
    negative = StrPattern("(?<!...)")

@implementer(Pattern)
class Yesno(PatternBase):
    choicepat = StrPattern("(?(id)yes_pattern|no_pattern)")

    def __init__(self, previous, yespattern, nopattern):
        self.pattern = choicepat.format(id=str(previous))
        self.yespattern = Pattern(yespattern)
        self.nopattern = Pattern(nopattern)

    def render(self):
        formatted = self.pattern.format(yes_pattern=self.yespattern.render(),
                            no_pattern=self.nopattern.render())
        return formatted.render()