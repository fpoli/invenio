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

from rply import ParserGenerator, LexerGenerator, Token


def generate_lexer():
    lg = LexerGenerator()
    lg.add(":", r":")
    lg.add("FIND", re.compile(r"\b(find|fin|f)\b", re.I))
    lg.add("->", r"->")
    lg.add("(", r"\(")
    lg.add(")", r"\)")
    lg.add("-", r"-")
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
    lg.add("SIMPLE_QUOTED_STRING", r"'[^']*'")
    lg.add("DOUBLE_QUOTED_STRING", r'"[^"]*"')
    lg.add("RE_STRING", r"/[^/]*/")
    lg.add("*", r"\*")
    # lg.add("NUMBER", r"\b\d+\b")
    # lg.add("WORD", r"[\w\d]+(?=:|\)|\s)")
    lg.add("WORD", r"[\w\d]+")
    lg.add("XWORD", r"[^\w\d\s]+")
    # lg.add("XWORD", r".+")

    lg.ignore(r"\s+")

    return lg.build()


def generate_parser(lexer):
    pg = ParserGenerator(["NUMBER", "PLUS", "MINUS"],
            precedence=[("left", ['PLUS', 'MINUS'])], cache_id="myparser")

    @pg.production("main : FIND KEYWORD VALUE")
    def main(p):
        print p



    return pg.build()


LEXER = generate_lexer()
# PARSER = generate_parser(LEXER)
PARSER = None


def lexQuery(query, lexer=LEXER):
    return lexer.lex(query)


def parseQuery(query, parser=PARSER):
    """Parse query string using given grammar"""
    return parser.parseString(query, parseAll=True)
