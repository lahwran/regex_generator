# Copyright (c) 2012
# Licensed under the terms of the MIT license; see LICENSE.txt

from .base import StrPattern, CharacterClass

anychar = StrPattern('.')

linestart = StrPattern('^')
lineend = StrPattern('$')

wordboundary = StrPattern("\\b")
nonwordboundary = StrPattern("\\B")

digit = CharacterClass("\\d")
nondigit = CharacterClass("\\D")

whitespace = CharacterClass("\\s")
nonwhitespace = CharacterClass("\\S")

alphanum = CharacterClass("\\w")
nonalphanum = CharacterClass("\\W")
