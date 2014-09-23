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

from pypeg2 import Keyword, maybe_some, optional, parse, Symbol, attr, Literal


from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer

import invenio.search_engine_spires_ast as ast


def generate_lexer(lg):
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


class UnaryOp(ast.UnaryOp):
    def __init__(self, args):
        # Also checks that len(args) == 1
        self.op, = args


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


class SingleQuotedString(UnaryOp):
    grammar = re.compile(r"'[^']*'")


class DoubleQuotedString(UnaryOp):
    grammar = re.compile(r'"[^"]*"')


class SlashQuotedString(UnaryOp):
    grammar = re.compile(r"/[^/]*/")


class SimpleValue(UnaryOp):
    grammar = re.compile(r"[^\s\)\(]+")


class SimpleRangeValue(UnaryOp):
    grammar = [SimpleValue, DoubleQuotedString]


class RangeValue(ast.BinaryOp):
    grammar = (
                attr('left', SimpleRangeValue),
                K('->'),
                attr('right', SimpleRangeValue)
              )


class Value(UnaryOp):
    grammar = [
        SingleQuotedString,
        DoubleQuotedString,
        SlashQuotedString,
        RangeValue,
        SimpleValue,
    ]


class Find(Keyword):
    regex = re.compile(r"(find|fin|f)", re.I)


class SimpleSpiresValue(UnaryOp):
    grammar = attr('op', [Value, Literal('('), Literal(')')])


class SpiresValue(ast.ListOp):
    grammar = maybe_some(SimpleSpiresValue, Whitespace), SimpleSpiresValue


class SpiresSimpleQuery(ast.BinaryOp):
    grammar = attr('left', Word), _, attr('right', SpiresValue)


class SpiresNotQuery(UnaryOp):
    pass


class SpiresParenthesizedQuery(UnaryOp):
    pass


class SpiresAndQuery(ast.BinaryOp):
    pass


class SpiresOrQuery(ast.BinaryOp):
    pass


class SpiresQuery(UnaryOp):
    grammar = attr('query', [
        SpiresNotQuery,
        SpiresParenthesizedQuery,
        SpiresAndQuery,
        SpiresOrQuery,
        SpiresSimpleQuery])

SpiresNotQuery.grammar = (
    Not,
    [
        (Whitespace, attr('op', SpiresSimpleQuery)),
        attr('op', SpiresParenthesizedQuery)
    ]
)
SpiresParenthesizedQuery.grammar = (
                                        K('('),
                                        _,
                                        attr('op', SpiresQuery),
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


class FindQuery(UnaryOp):
    grammar = Find, Whitespace, attr('query', SpiresQuery), _

    def __init__(self, args):
        _, _, op, _ = args
        super(FindQuery, self).__init__(op)


class Main(UnaryOp):
    grammar = _, [Query, FindQuery], _


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
    return parse(query, parser, whitespace="")
