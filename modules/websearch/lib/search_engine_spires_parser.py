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

import pypeg2
from pypeg2 import (Keyword, maybe_some, optional, attr,
                    Literal, omit, some)


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


class LeafRule(ast.Leaf):

    def __init__(self):
        pass


class UnaryRule(ast.UnaryOp):

    def __init__(self):
        pass


class BinaryRule(ast.BinaryOp):

    def __init__(self):
        pass


class Whitespace(LeafRule):
    grammar = attr('value', re.compile(r"\s+"))


_ = optional(Whitespace)


class Not(object):
    grammar = omit([re.compile(r"not", re.I), Literal('-')])


class And(object):
    grammar = omit([re.compile(r"and", re.I), Literal('+')])


class Or(object):
    grammar = omit([re.compile(r"or", re.I), Literal('|')])


class Word(LeafRule):
    grammar = attr('value', re.compile(r"[\w\d]+"))


class SingleQuotedString(LeafRule):
    grammar = Literal("'"), attr('value', re.compile(r"[^']*")), Literal("'")


class DoubleQuotedString(LeafRule):
    grammar = Literal('"'), attr('value', re.compile(r'[^"]*')), Literal('"')


class SlashQuotedString(LeafRule):
    grammar = Literal('/'), attr('value', re.compile(r"[^/]*")), Literal('/')


class SimpleValue(LeafRule):

    def __init__(self, values):
        super(SimpleValue, self).__init__()
        self.value = "".join(v.value for v in values)


class SimpleValueUnit(LeafRule):
    grammar = [
        re.compile(r"[^\s\)\(:]+"),
        (re.compile(r'\('), SimpleValue, re.compile(r'\)')),
    ]

    def __init__(self, args):
        super(SimpleValueUnit, self).__init__()
        if isinstance(args, basestring):
            self.value = args
        else:
            self.value = args[0] + args[1].value + args[2]


SimpleValue.grammar = some(SimpleValueUnit)


class SpiresSimpleValue(LeafRule):

    def __init__(self, values):
        super(SpiresSimpleValue, self).__init__()
        self.value = "".join(v.value for v in values)


class SpiresSimpleValueUnit(LeafRule):
    grammar = [
        re.compile(r"[^\s\)\(]+"),
        (re.compile(r'\('), SpiresSimpleValue, re.compile(r'\)')),
    ]

    def __init__(self, args):
        super(SpiresSimpleValueUnit, self).__init__()
        if isinstance(args, basestring):
            self.value = args
        else:
            self.value = args[0] + args[1].value + args[2]


SpiresSimpleValue.grammar = some(SpiresSimpleValueUnit)


class SimpleRangeValue(LeafRule):
    grammar = attr('value', re.compile(r"([^\s\)\(-]|-+[^\s\)\(>])+"))


class RangeValue(UnaryRule):
    grammar = attr('op', [DoubleQuotedString, SimpleRangeValue])


class RangeOp(BinaryRule):
    grammar = (
        attr('left', RangeValue),
        Literal('->'),
        attr('right', RangeValue)
    )


class Value(UnaryRule):
    grammar = attr('op', [
        RangeOp,
        SingleQuotedString,
        DoubleQuotedString,
        SlashQuotedString,
        SimpleValue,
    ])


class Find(Keyword):
    regex = re.compile(r"(find|fin|f)", re.I)


class SpiresSmartValue(UnaryRule):

    @classmethod
    def parse(cls, parser, text, pos):  # pylint: disable=W0613
        """Match simple values excluding some Keywords like 'and' and 'or'"""
        if not text.strip():
            return text, SyntaxError("Invalid value")

        class Rule(object):
            grammar = attr('value', SpiresSimpleValue), omit(re.compile(".*"))

        try:
            tree = pypeg2.parse(text, Rule, whitespace="")
        except SyntaxError:
            return text, SyntaxError("Expected %r" % cls)
        else:
            r = tree.value

        if r.value.lower() in ('and', 'or', 'not'):
            return text, SyntaxError("Invalid value %s" % r.value)

        return text[len(r.value):], r


class SpiresValue(ast.ListOp):
    grammar = [
        (SpiresSmartValue, maybe_some(Whitespace, SpiresSmartValue)),
        Value,
    ]


class SpiresSimpleQuery(BinaryRule):
    pass


class SpiresNotQuery(UnaryRule):
    pass


class SpiresParenthesizedQuery(UnaryRule):
    pass


class SpiresAndQuery(BinaryRule):
    pass


class SpiresOrQuery(BinaryRule):
    pass


class SpiresQuery(UnaryRule):
    grammar = attr('op', [
        SpiresNotQuery,
        SpiresAndQuery,
        SpiresOrQuery,
        SpiresParenthesizedQuery,
        SpiresSimpleQuery])


class NestableKeyword(LeafRule):
    grammar = attr('value', [re.compile('refersto', re.I), ])


SpiresSimpleQuery.grammar = [
        (
            attr('left', NestableKeyword),
            [
                omit(_, Literal(':'), _),
                omit(Whitespace),
            ],
            attr('right', [SpiresParenthesizedQuery, SpiresSimpleQuery]),
        ),
        (
            attr('left', Word),
            omit(_, Literal(':'), _),
            attr('right', Value)
        ),
        (
            attr('left', Word),
            omit(Whitespace),
            attr('right', SpiresValue)
        ),
    ]


SpiresNotQuery.grammar = (
        omit(re.compile(r"not", re.I)),
        [
            (omit(Whitespace), attr('op', SpiresSimpleQuery)),
            (omit(_), attr('op', SpiresParenthesizedQuery)),
        ],
)

SpiresParenthesizedQuery.grammar = (
    omit(Literal('('), _),
    attr('op', SpiresQuery),
    omit(_, Literal(')')),
)

SpiresAndQuery.grammar = (
    [
        (attr('left', SpiresParenthesizedQuery), omit(_)),
        (attr('left', SpiresSimpleQuery), omit(Whitespace)),
    ],
    omit(re.compile(r"and", re.I)),
    [
        (omit(Whitespace), attr('right', SpiresQuery)),
        (omit(_), attr('right', SpiresParenthesizedQuery)),
    ]
)

SpiresOrQuery.grammar = (
    [
        (attr('left', SpiresParenthesizedQuery), omit(_)),
        (attr('left', SpiresSimpleQuery), omit(Whitespace)),
    ],
    omit(re.compile(r"or", re.I)),
    [
        (omit(Whitespace), attr('right', SpiresQuery)),
        (omit(_), attr('right', SpiresParenthesizedQuery)),
    ]
)


class Query(UnaryRule):
    pass


class ValueQuery(UnaryRule):
    grammar = attr('op', Value)


class KeywordQuery(BinaryRule):
    pass

KeywordQuery.grammar = [
    (
        attr('left', Word),
        omit(_, Literal(':'), _),
        attr('right', KeywordQuery)
    ),
    (
        attr('left', Word),
        omit(_, Literal(':'), _),
        attr('right', Value)
    ),
    (
        attr('left', Word),
        omit(_, Literal(':'), _),
        attr('right', Query)
    ),
]


class SimpleQuery(UnaryRule):
    grammar = attr('op', [KeywordQuery, ValueQuery])


class NotQuery(UnaryRule):
    pass


class ParenthesizedQuery(UnaryRule):
    pass


class AndQuery(BinaryRule):
    pass


class ImplicitAndQuery(BinaryRule):
    pass


class OrQuery(BinaryRule):
    pass


Query.grammar = attr('op', [
    NotQuery,
    AndQuery,
    OrQuery,
    ImplicitAndQuery,
    ParenthesizedQuery,
    SimpleQuery
])


NotQuery.grammar = [
    (
        omit(Not),
        [
            (omit(Whitespace), attr('op', Query)),
            (omit(_), attr('op', ParenthesizedQuery)),
        ],
    ),
    (
        omit(Literal('-')),
        attr('op', Query),
    ),
]
ParenthesizedQuery.grammar = omit(
    Literal('('), _), attr('op', Query), omit(_, Literal(')'))
AndQuery.grammar = [
    (
        [
            (attr('left', ParenthesizedQuery), omit(_)),
            (attr('left', SimpleQuery), omit(Whitespace)),
        ],
        omit(And),
        [
            (omit(Whitespace), attr('right', Query)),
            (omit(_), attr('right', ParenthesizedQuery)),
        ],
    ),
    (
        [
            (attr('left', ParenthesizedQuery), omit(_)),
            (attr('left', SimpleQuery), omit(Whitespace)),
        ],
        omit(Literal('+')),
        attr('right', Query),
    ),
]
ImplicitAndQuery.grammar = (
    [
        attr('left', ParenthesizedQuery),
        (attr('left', SimpleQuery), omit(Whitespace)),
    ],
    attr('right', Query),
)
OrQuery.grammar = [
    (
        [
            (attr('left', ParenthesizedQuery), omit(_)),
            (attr('left', SimpleQuery), omit(Whitespace)),
        ],
        omit(Or),
        [
            (omit(Whitespace), attr('right', Query)),
            (omit(_), attr('right', ParenthesizedQuery)),
        ],
    ),
    (
        [
            (attr('left', ParenthesizedQuery), omit(_)),
            (attr('left', SimpleQuery), omit(Whitespace)),
        ],
        omit(Literal('|')),
        attr('right', Query),
    ),
]


class FindQuery(UnaryRule):
    grammar = omit(Find, Whitespace), attr('op', SpiresQuery)


class Main(UnaryRule):
    grammar = omit(_), attr('op', [FindQuery, Query]), omit(_)


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


def parseQuery(query, parser=PARSER):
    """Parse query string using given grammar"""
    return pypeg2.parse(query, parser, whitespace="")
