# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import re

from rply import ParserGenerator, LexerGenerator
# for reimporting
from rply import Token  # pylint: disable=W0611


from invenio.search_engine_spires_ast import (KeywordOp, AndOp, OrOp, NotOp,
                                              Keyword, SingleQuotedValue,
                                              DoubleQuotedValue, Value,
                                              RegexValue, RangeOp)


def generate_lexer():
    lg = LexerGenerator()
    lg.add("COLON", r":")
    lg.add("FIND", re.compile(r"\b(find|fin|f)\b", re.I))
    lg.add("->", r"->")
    lg.add("(", r"\(")
    lg.add(")", r"\)")
    lg.add("AND", re.compile(r"\band\b", re.I))
    lg.add("OR", re.compile(r"\bor\b", re.I))
    lg.add("|", r"\|")
    lg.add("<=", r"<=")
    lg.add(">=", r">=")
    lg.add(">", r">")
    lg.add("<", r"<")
    lg.add("+", r"\+")
    lg.add("AFTER", re.compile(r"\bafter\b", re.I))
    lg.add("BEFORE", re.compile(r"\bbefore\b", re.I))
    lg.add("NOT", re.compile(r"\bnot\b", re.I))
    # re to match escapes
    # r'"([^\"]|\\.)*([^\\]|\\)"'
    lg.add("SINGLE_QUOTED_STRING", r"'[^']*'")
    lg.add("DOUBLE_QUOTED_STRING", r'"[^"]*"')
    lg.add("REGEX_STRING", r"/[^/]*/")
    lg.add("*", r"\*")
    # lg.add("NUMBER", r"\b\d+\b")
    # lg.add("WORD", r"[\w\d]+(?=:|\)|\s)")
    lg.add('KEYWORD', r'foo')
    lg.add('-KEYWORD', r'-foo')
    lg.add("-", r"-")
    lg.add("WORD", r"[\w\d]+")
    lg.add("XWORD", r"[^\w\d\s]+")
    # lg.add("XWORD", r".+")

    lg.ignore(r"\s+")

    return lg.build()


def generate_parser(lexer, cache_id):
    pg = ParserGenerator([rule.name for rule in lexer.rules], cache_id=cache_id)

    @pg.production("main : query")
    def main(p):  # pylint: disable=W0612
        return p[0]

    @pg.production("query : ( query )")
    def query1(p):  # pylint: disable=W0612
        return p[1]

    @pg.production("query : simple_query AND query")
    def query2(p):  # pylint: disable=W0612
        return AndOp(p[0], p[2])

    @pg.production("query : simple_query OR query")
    @pg.production("query : simple_query | query")
    def query3(p):  # pylint: disable=W0612
        return OrOp(p[0], p[2])

    @pg.production("query : NOT simple_query")
    @pg.production("query : - simple_query")
    def query4(p):  # pylint: disable=W0612
        return NotOp(p[1])

    @pg.production("query : simple_query query")
    def query5(p):  # pylint: disable=W0612
        return AndOp(p[0], p[1])

    @pg.production("query : simple_query")
    def query6(p):  # pylint: disable=W0612
        return p[0]

    @pg.production("simple_query : KEYWORD COLON keyword_value")
    def simple_query(p):  # pylint: disable=W0612
        keyword = Keyword(p[0].value)
        return KeywordOp(keyword, p[2])

    @pg.production("simple_query : -KEYWORD COLON keyword_value")
    def simple_query(p):  # pylint: disable=W0612
        keyword = Keyword(p[0].value[1:])
        return NotOp(KeywordOp(keyword, p[2]))

    @pg.production("simple_query : keyword_value")
    def simple_query(p):  # pylint: disable=W0612
        return p[0]

    @pg.production("keyword_value : SINGLE_QUOTED_STRING")
    def keyword_value1(p):  # pylint: disable=W0612
        return SingleQuotedValue(p[0].value[1:-1])

    @pg.production("keyword_value : DOUBLE_QUOTED_STRING")
    def keyword_value2(p):  # pylint: disable=W0612
        return DoubleQuotedValue(p[0].value[1:-1])

    @pg.production("keyword_value : REGEX_STRING")
    def keyword_value3(p):  # pylint: disable=W0612
        return RegexValue(p[0].value[1:-1])

    @pg.production("keyword_value : range_value -> range_value")
    def keyword_value4(p):  # pylint: disable=W0612
        return RangeOp(p[0], p[2])

    @pg.production("keyword_value : value")
    def keyword_value5(p):  # pylint: disable=W0612
        return p[0]

    @pg.production("end_value_unit : WORD")
    @pg.production("end_value_unit : XWORD")
    @pg.production("end_value_unit : (")
    @pg.production("end_value_unit : )")
    @pg.production("end_value_unit : *")
    @pg.production("end_value_unit : <")
    @pg.production("end_value_unit : <=")
    @pg.production("end_value_unit : >")
    @pg.production("end_value_unit : >=")
    def value_unit(p):  # pylint: disable=W0612
        print 'p', p
        print 'value_unit', p
        return p[0]

    @pg.production("value_unit : end_value_unit")
    @pg.production("value_unit : -")
    def rule(p):  # pylint: disable=W0612
        print 'value_unit', p[0].value
        return p[0].value

    @pg.production("range_value : value")
    def range_value(p):  # pylint: disable=W0612
        return p[0]

    @pg.production("value : value_unit value")
    def value(p):  # pylint: disable=W0612
        print 'value : value_unit value', p
        return Value(p[0] + p[1].value)

    @pg.production("value : value_unit")
    def value(p):  # pylint: disable=W0612
        print 'value : value_unit', p
        return Value(p[0])

    @pg.error
    def error_handler(token):  # pylint: disable=W0612
        raise ValueError("Ran into a %s where it wasn't expected" % token.gettokentype())

    return Parser(lexer, pg.build())


class Parser(object):
    def __init__(self, lexer, parser):
        self.lexer = lexer
        self.parser = parser

    def parse(self, query):
        tokens = list(self.lexer.lex(query))
        print 'tokens', tokens
        return self.parser.parse(iter(tokens))


LEXER = generate_lexer()
PARSER = generate_parser(LEXER, cache_id="parser")


def lexQuery(query, lexer=LEXER):
    return lexer.lex(query)


def parseQuery(query, parser=PARSER):
    """Parse query string using given grammar"""
    return parser.parse(query)
