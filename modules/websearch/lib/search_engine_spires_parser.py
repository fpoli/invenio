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

from pypeg2 import Keyword, maybe_some, some, optional, parse, Symbol


from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer

import invenio.search_engine_spires_ast as ast


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


class Not(object):
    grammar = [re.compile(r"not", re.I), K('-')]


class And(object):
    grammar = [re.compile(r"and", re.I), K('+')]


class Or(object):
    grammar = [re.compile(r"or", re.I), K('|')]


class Word(Symbol):
    regex = re.compile(r"[\w\d]+")


class SingleQuotedString(object):
    grammar = re.compile(r"'[^']*'")


class DoubleQuotedString(object):
    grammar = re.compile(r'"[^"]*"')


class SlashQuotedString(object):
    grammar = re.compile(r"/[^/]*/")


class SimpleValue(ast.Leaf):
    grammar = re.compile(r"[^\s\)\(]+")

    def __init__(self, value):
        self.value = value


class SimpleRangeValue(ast.UnaryOp):
    grammar = [SimpleValue, DoubleQuotedString]

    def __init__(self, value):
        self.value = value


class RangeValue(object):
    grammar = SimpleRangeValue, K('->'), SimpleRangeValue


class Value(object):
    grammar = [
        SingleQuotedString,
        DoubleQuotedString,
        SlashQuotedString,
        RangeValue,
        SimpleValue,
    ]

    def __new__(cls, value):
        return value


class Find(object):
    grammar = re.compile(r"(find|fin|f)", re.I)


class SimpleSpiresValue(object):
    grammar = [Value, K('('), K(')')]


class SpiresValue(object):
    grammar = maybe_some(SimpleSpiresValue, Whitespace), SimpleSpiresValue


class SpiresSimpleQuery(object):
    grammar = Word, _, SpiresValue


class SpiresNotQuery(object):
    pass


class SpiresParenthesizedQuery(object):
    pass


class SpiresAndQuery(object):
    pass


class SpiresOrQuery(object):
    pass


class SpiresQuery(object):
    grammar = [
        SpiresNotQuery,
        SpiresParenthesizedQuery,
        SpiresAndQuery,
        SpiresOrQuery,
        SpiresSimpleQuery]

SpiresNotQuery.grammar = (
    Not,
    [
        (Whitespace, SpiresSimpleQuery),
        SpiresParenthesizedQuery
    ]
)
SpiresParenthesizedQuery.grammar = K('('), _, SpiresQuery, _, K(')')
SpiresAndQuery.grammar = (
    [
        SpiresParenthesizedQuery,
        (SpiresSimpleQuery, Whitespace)
    ],
    And,
    [
        (Whitespace, SpiresQuery),
        SpiresParenthesizedQuery
    ]
)
SpiresOrQuery.grammar = (
    [
        SpiresParenthesizedQuery,
        (SpiresSimpleQuery, Whitespace)
    ],
    Or,
    [(Whitespace, SpiresQuery), SpiresParenthesizedQuery]
)


class ValueQuery(ast.UnaryOp):
    grammar = Value


class KeywordQuery(object):
    grammar = Word, _, K(':'), _, Value


class SimpleQuery(object):
    grammar = [KeywordQuery, ValueQuery]

    def __new__(cls, query):
        return query


class NotQuery(object):
    pass


class ParenthesizedQuery(object):

    def __new__(cls, query):
        return query


class AndQuery(ast.BinaryOp):

    def __init__(self, args):
        left, _, right = args
        super(AndQuery, self).__init__(left, right)


class ImplicitAndQuery(object):

    def __new__(cls, args):
        return AndQuery(args)


class OrQuery(object):
    pass


class Query(object):
    grammar = [
        NotQuery,
        ParenthesizedQuery,
        AndQuery,
        OrQuery,
        ImplicitAndQuery,
        SimpleQuery
    ]

    def __new__(cls, query):
        return query


NotQuery.grammar = (
    Not,
    [
        (Whitespace, SimpleQuery),
        ParenthesizedQuery
    ]
)
ParenthesizedQuery.grammar = K('('), _, Query, _, K(')')
AndQuery.grammar = (
    [
        ParenthesizedQuery,
        (SimpleQuery, Whitespace)
    ],
    And,
    [
        (Whitespace, Query),
        ParenthesizedQuery
    ]
)
ImplicitAndQuery.grammar = (
    [
        ParenthesizedQuery,
        (SimpleQuery, Whitespace)
    ],
    [
        Query,
        ParenthesizedQuery
    ]
)
OrQuery.grammar = (
    [
        ParenthesizedQuery,
        (SimpleQuery, Whitespace)
    ],
    Or,
    [
        (Whitespace, Query),
        ParenthesizedQuery
    ]
)


class FindQuery(object):
    grammar = Find, Whitespace, SpiresQuery, _


class Main(object):
    grammar = _, [Query, FindQuery], _

    def __new__(cls, query):
        return query

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
