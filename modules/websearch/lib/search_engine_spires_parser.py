# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2014 CERN.
##
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
##
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
##
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import os
import re
import traceback

from pypeg2 import Keyword, maybe_some, optional, parse, Symbol, attr


from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer


def generate_lexer():
    # lg.add(")", r"\)(?=\)*(\s|$))")
    lg.add("<=", r"<=")
    lg.add(">=", r">=")
    lg.add(">", r">")
    lg.add("<", r"<")
    lg.add("+", r"\+")
    lg.add("AFTER", re.compile(r"\bafter\b", re.I))
    lg.add("BEFORE", re.compile(r"\bbefore\b", re.I))
    # re to match escapes
    # r'"([^\"]|\\.)*([^\\]|\\)"'
    lg.add("*", r"\*")
    lg.add("-", r"-")

    # pylint: disable=C0321,R0903


class Whitespace(object):
    grammar = re.compile(r"\s+")

    def __init__(self, value):
        self.value = value

_ = optional(Whitespace)
K = Keyword


class Not(Keyword):
    grammar = [re.compile(r"not", re.I), K('-')]


class And(Keyword):
    grammar = [re.compile(r"and", re.I), K('+')]


class Or(object):
    grammar = [re.compile(r"or", re.I), K('|')]


class Word(Symbol):
    regex = re.compile(r"[\w\d]+")


class SingleQuotedString(object):
    grammar = attr('value', re.compile(r"'[^']*'"))


class DoubleQuotedString(object):
    grammar = attr('value', re.compile(r'"[^"]*"'))


class SlashQuotedString(object):
    grammar = attr('value', re.compile(r"/[^/]*/"))


class SimpleValue(object):
    grammar = attr('value', re.compile(r"[^\s\)\(]+"))

    def __init__(self, value):
        self.value = value


class SimpleRangeValue(object):
    grammar = attr('value', [SimpleValue, DoubleQuotedString])

    def __init__(self, value):
        self.value = value


class RangeValue(object):
    grammar = attr('start', SimpleRangeValue), K(
        '->'), attr('end', SimpleRangeValue)


class Value(object):
    grammar = attr('value', [
        SingleQuotedString,
        DoubleQuotedString,
        SlashQuotedString,
        RangeValue,
        SimpleValue,
    ])

    def __new__(cls, value):
        return value


class Find(Keyword):
    regex = re.compile(r"(find|fin|f)", re.I)


class SimpleSpiresValue(object):
    grammar = attr('value', [Value, K('('), K(')')])


class SpiresValue(object):
    grammar = maybe_some(SimpleSpiresValue, Whitespace), SimpleSpiresValue

    def __init__(self, args):
        self.value = "".join(args)


class SpiresSimpleQuery(object):
    grammar = attr('keyword', Word), _, attr('value', SpiresValue)


class SpiresNotQuery(object):
    pass


class SpiresParenthesizedQuery(object):
    pass


class SpiresAndQuery(object):
    pass


class SpiresOrQuery(object):
    pass


class SpiresQuery(object):
    grammar = attr('query', [
        SpiresNotQuery,
        SpiresParenthesizedQuery,
        SpiresAndQuery,
        SpiresOrQuery,
        SpiresSimpleQuery])

SpiresNotQuery.grammar = (
    Not,
    [
        (Whitespace, attr('query', SpiresSimpleQuery)),
        attr('query', SpiresParenthesizedQuery)
    ]
)
SpiresParenthesizedQuery.grammar = (
                                        K('('),
                                        _,
                                        attr('query', SpiresQuery),
                                        _,
                                        K(')')
                                    )
SpiresAndQuery.grammar = (
    [
        attr('left', SpiresParenthesizedQuery),
        (attr('left', SpiresSimpleQuery), Whitespace)
    ],
    And,
    [
        (Whitespace, attr('right', SpiresQuery)),
        attr('right', SpiresParenthesizedQuery)
    ]
)
SpiresOrQuery.grammar = (
    [
        attr('left', SpiresParenthesizedQuery),
        (attr('left', SpiresSimpleQuery), Whitespace)
    ],
    Or,
    [
        (Whitespace, attr('right', SpiresQuery)),
        attr('right', SpiresParenthesizedQuery)
    ]
)


class ValueQuery(object):
    grammar = attr('value', Value)


class KeywordQuery(object):
    grammar = attr('keyword', Word), _, K(':'), _, attr('value', Value)


class SimpleQuery(object):
    grammar = attr('query', [KeywordQuery, ValueQuery])


class NotQuery(object):
    pass


class ParenthesizedQuery(object):
    pass


class AndQuery(object):
    pass


class ImplicitAndQuery(object):
    pass


class OrQuery(object):
    pass


class Query(object):
    grammar = attr('query', [
        NotQuery,
        ParenthesizedQuery,
        AndQuery,
        OrQuery,
        ImplicitAndQuery,
        SimpleQuery
    ])


NotQuery.grammar = (
    Not,
    [
        (Whitespace, attr('query', SimpleQuery)),
        attr('query', ParenthesizedQuery)
    ]
)
ParenthesizedQuery.grammar = K('('), _, attr('query', Query), _, K(')')
AndQuery.grammar = (
    [
        attr('left', ParenthesizedQuery),
        (attr('left', SimpleQuery), Whitespace)
    ],
    And,
    [
        (Whitespace, attr('right', Query)),
        attr('right', ParenthesizedQuery)
    ]
)
ImplicitAndQuery.grammar = (
    [
        attr('left', ParenthesizedQuery),
        (attr('left', SimpleQuery), Whitespace)
    ],
    attr('right', Query),
)
OrQuery.grammar = (
    [
        attr('left', ParenthesizedQuery),
        (attr('left', SimpleQuery), Whitespace)
    ],
    Or,
    [
        (Whitespace, attr('right', Query)),
        attr('right', ParenthesizedQuery)
    ]
)


class FindQuery(object):
    grammar = Find, Whitespace, attr('query', SpiresQuery), _


class Main(object):
    grammar = _, attr('query', [Query, FindQuery]), _


# pylint: enable=C0321,R0903


def generate_parser():
    return Main


def load_walkers():

    def cb_plugin_builder(plugin_name, plugin_code):
        return getattr(plugin_code, "plugin_class")

    plugin_dir = os.path.join(CFG_PYLIBDIR,
                              "invenio",
                              "search_parser_ast_walkers",
                              "*.py")
    # Load plugins
    plugins = PluginContainer(plugin_dir,
                              plugin_builder=cb_plugin_builder)

    # Check for broken plug-ins
    broken = plugins.get_broken_plugins()
    for plugin, info in broken.items():
        traceback_str = "".join(traceback.format_exception(*info))
        raise Exception("Failed to load %s:\n %s" % (plugin, traceback_str))

    return plugins.get_enabled_plugins()


PARSER = generate_parser()
WALKERS = load_walkers()


def parseQuery(query, parser=PARSER):
    """Parse query string using given grammar"""
    return parse(query, parser, whitespace="")[0]
