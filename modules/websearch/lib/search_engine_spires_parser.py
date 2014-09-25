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

SPIRES_KEYWORDS = [
# address
'address',
# affiliation
'affiliation', 'affil', 'aff', 'af', 'institution', 'inst',
# any field
'anyfield', 'any',
# author count
'authorcount', 'ac',
# bulletin
'bb', 'bbn', 'bull', 'bulletin-bd', 'bulletin-bd-no', 'eprint',
# citation / reference
'reference', 'c', 'citation', 'cited', 'jour-vol-page', 'jvp',
# collaboration
'collaboration', 'collab-name', 'cn',
# conference number
'confnumber', 'conf-number', 'cnum',
# country
'country', 'cc',
# date
'date', 'd',
# date added
'date-added', 'dadd', 'da',
# date updated
'date-updated', 'dupd', 'du',
# first author
'firstauthor', 'first-author', 'fa',
# author
'a', 'au', 'author', 'name',
# exact author
'exactauthor', 'exact-author', 'ea',
# experiment
'exp', 'experiment', 'expno', 'sd', 'se',
# journal
'journal', 'j', 'published_in', 'spicite', 'volume', 'vol',
# journal page
'journalpage', 'journal-page', 'jp',
# journal year
'journal-year', 'jy',
# key
'key', 'irn', 'record', 'document', 'documents',
# keywords
'keyword', 'k', 'keywords', 'kw',
# note
'note',
# old title
'old-title', 'old-t', 'ex-ti', 'et',
#postal code
'postalcode', 'zip',
# ppf subject
'ppf-subject', 'status',
# recid
'recid',
# report number
'r', 'rn', 'rept', 'report', 'report-num', 'reportnumber',
# title
't', 'ti', 'title', 'with-language',
# fulltext
'fulltext', 'ft',
# topic
'topic', 'tp', 'hep-topic', 'desy-keyword', 'dk',
# doi
'doi',
# topcite
'cited', 'topcit', 'topcite',
# captions
'caption',
# category
'arx', 'category',
# primarch
'parx', 'primarch',
# texkey
'texkey',
# type code
'collection', 'tc', 'ty', 'type', 'type-code', 'scl', 'ps',
# field code
'f', 'fc', 'field', 'field-code', 'subject',
# coden
'journal', 'bc', 'browse-only-indx', 'coden', 'journal-coden',
# jobs specific codes
'title', 'job', 'position', 'region', 'continent', 'deadline', 'rank',
# cataloguer
'cataloguer', 'cat',
# replace all the keywords without match with empty string
# this will remove the noise from the unknown keywrds in the search
# and will in all fields for the words following the keywords
# energy
'e', 'energy', 'energyrange-code',
# exact experiment number
'ee', 'exact-exp', 'exact-expno',
# hidden note
'hidden-note', 'hn',
# ppf
'ppf', 'ppflist',
# slac topics
'ppfa', 'slac-topics', 'special-topics', 'stp',
# test index
'test', 'testindex',
]


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


class ListRule(ast.ListOp):

    def __init__(self):
        pass


class Whitespace(LeafRule):
    grammar = attr('value', re.compile(r"\s+"))


_ = optional(Whitespace)


class Not(object):
    grammar = omit([
        omit(re.compile(r"and\s+not", re.I)),
        re.compile(r"not", re.I),
        Literal('-'),
    ])


class And(object):
    grammar = omit([
        re.compile(r"and", re.I),
        Literal('+'),
    ])


class Or(object):
    grammar = omit([
        re.compile(r"or", re.I),
        Literal('|'),
    ])


class Word(LeafRule):
    grammar = attr('value', re.compile(r"[\w\d]+"))


class SingleQuotedString(LeafRule):
    grammar = Literal("'"), attr('value', re.compile(r"[^']*")), Literal("'")


class DoubleQuotedString(LeafRule):
    # TODO: can be improved with r'"([^\"]|\\.)*([^\\]|\\)"'
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


class SpiresQuery(ListRule):
    pass


class SpiresParenthesizedQuery(UnaryRule):
    grammar = (
        omit(Literal('('), _),
        attr('op', SpiresQuery),
        omit(_, Literal(')')),
    )


class SpiresNotQuery(UnaryRule):
    grammar = (
            [
                omit(re.compile(r"and\s+not", re.I)),
                omit(re.compile(r"not", re.I)),
            ],
            [
                (omit(Whitespace), attr('op', SpiresSimpleQuery)),
                (omit(_), attr('op', SpiresParenthesizedQuery)),
            ],
    )


class SpiresAndQuery(UnaryRule):
    grammar = (
        omit(re.compile(r"and", re.I)),
        [
            (omit(Whitespace), attr('op', SpiresSimpleQuery)),
            (omit(_), attr('op', SpiresParenthesizedQuery)),
        ]
    )


class SpiresOrQuery(UnaryRule):
    grammar = (
        omit(re.compile(r"or", re.I)),
        [
            (omit(Whitespace), attr('op', SpiresSimpleQuery)),
            (omit(_), attr('op', SpiresParenthesizedQuery)),
        ]
    )


SpiresQuery.grammar = attr('children', (
    [
        SpiresParenthesizedQuery,
        SpiresSimpleQuery,
    ],
    maybe_some((
        omit(_),
        [
            SpiresNotQuery,
            SpiresAndQuery,
            SpiresOrQuery,
        ]
    )),
))


class NestableKeyword(LeafRule):
    grammar = attr('value', [re.compile('refersto', re.I), ])


class GreaterQuery(UnaryRule):
    grammar = (
        omit([
            Literal('>'),
            re.compile('after', re.I)
        ], _),
        attr('op', SpiresValue)
    )


class Number(LeafRule):
    grammar = attr('value', re.compile(r'\d+'))


class GreaterEqualQuery(UnaryRule):
    grammar = [
        (omit(Literal('>='), _), attr('op', SpiresValue)),
        (attr('op', Number), omit(re.compile(r'\+(?=\s|\)|$)'))),
    ]


class LowerQuery(UnaryRule):
    grammar = (
        omit([
            Literal('<'),
            re.compile('before', re.I)
        ], _),
        attr('op', SpiresValue)
    )


class LowerEqualQuery(UnaryRule):
    grammar = [
        (omit(Literal('<='), _), attr('op', SpiresValue)),
        (attr('op', Number), omit(re.compile(r'\-(?=\s|\)|$)'))),
    ]


class ValueQuery(UnaryRule):
    grammar = attr('op', Value)


class SpiresValueQuery(UnaryRule):
    grammar = attr('op', SpiresValue)


SpiresSimpleQuery.grammar = [
        (
            attr('left', NestableKeyword),
            omit(_, Literal(':'), _),
            attr('right', [
                 SpiresParenthesizedQuery,
                 SpiresSimpleQuery,
                 ValueQuery]),
        ),
        (
            attr('left', NestableKeyword),
            omit(Whitespace),
            attr('right', [
                 SpiresParenthesizedQuery,
                 SpiresSimpleQuery,
                 SpiresValueQuery]),
        ),
        (
            attr('left', Word),
            omit(_, Literal(':'), _),
            attr('right', Value)
        ),
        (
            attr('left', Word),
            omit(Whitespace),
            attr('right', [
                GreaterEqualQuery,
                GreaterQuery,
                LowerEqualQuery,
                LowerQuery,
                SpiresValue])
        ),
    ]


class Query(ListRule):
    pass


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


class ParenthesizedQuery(UnaryRule):
    grammar = (
        omit(Literal('('), _),
        attr('op', Query),
        omit(_, Literal(')')),
    )


class NotQuery(UnaryRule):
    grammar = [
        (
            omit(Not),
            [
                (omit(Whitespace), attr('op', SimpleQuery)),
                (omit(_), attr('op', ParenthesizedQuery)),
            ],
        ),
        (
            omit(Literal('-')),
            attr('op', SimpleQuery),
        ),
    ]


class AndQuery(UnaryRule):
    grammar = [
        (
            omit(And),
            [
                (omit(Whitespace), attr('op', SimpleQuery)),
                (omit(_), attr('op', ParenthesizedQuery)),
            ],
        ),
        (
            omit(Literal('+')),
            attr('op', SimpleQuery),
        ),
    ]


class ImplicitAndQuery(UnaryRule):
    grammar = [
        attr('op', ParenthesizedQuery),
        attr('op', SimpleQuery),
    ]


class OrQuery(UnaryRule):
    grammar = [
        (
            omit(Or),
            [
                (omit(Whitespace), attr('op', SimpleQuery)),
                (omit(_), attr('op', ParenthesizedQuery)),
            ],
        ),
        (
            omit(Literal('|')),
            attr('op', SimpleQuery),
        ),
    ]


Query.grammar = attr('children', (
    [
        ParenthesizedQuery,
        SimpleQuery,
    ],
    maybe_some((
        omit(_),
        [
        NotQuery,
        AndQuery,
        OrQuery,
        ImplicitAndQuery,
    ])),
))


class FindQuery(UnaryRule):
    grammar = omit(Find, Whitespace), attr('op', SpiresQuery)


class EmptyQueryRule(LeafRule):
    grammar = attr('value', re.compile(r'\s*'))


class Main(UnaryRule):
    grammar = [
        (omit(_), attr('op', [FindQuery, Query]), omit(_)),
        attr('op', EmptyQueryRule),
    ]


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


class SpiresToInvenioSyntaxConverter(object):
    def __init__(self):
        self.parser = generate_parser()
        self.walkers = load_walkers()

    def parse_query(self, query):
        """Parse query string using given grammar"""
        tree = pypeg2.parse(query, self.parser, whitespace="")
        converter = self.walkers['pypeg_to_ast_converter']()
        return tree.accept(converter)

    def convert_query(self, query):
        tree = self.parse_query(query)
        converter = self.walkers['spires_to_invenio_converter']()
        printer = self.walkers['repr_printer']()
        return tree.accept(converter).accept(printer)
