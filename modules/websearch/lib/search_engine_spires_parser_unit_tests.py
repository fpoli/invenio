# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2010, 2011, 2012, 2013 CERN.
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

"""Unit tests for the search engine query parsers."""


from invenio.testutils import (make_test_suite,
                               run_test_suite,
                               InvenioTestCase,
                               nottest)
from invenio.search_engine_spires_parser import (parseQuery,
                                                 lexQuery,
                                                 Token)


@nottest
def generate_lexer_test(query, expected):
    def func(self):
        output = list(lexQuery(query))
        self.assertEqual(output, expected)
    return func


@nottest
def generate_parser_test(query, expected):
    def func(self):
        output = list(parseQuery(query))
        print output
        self.assertEqual(output, expected)
    return func


@nottest
def generate_tests(generate_test):
    def fun(cls):
        for count, (query, expected) in enumerate(cls.queries):
            func = generate_test(query, expected)
            func.__name__ = 'test_%s' % count
            func.__doc__ = "Parsing query %s" % query
            setattr(cls, func.__name__, func)
        return cls
    return fun


@generate_tests(generate_lexer_test)  # pylint: disable=R0903
class TestLexer(InvenioTestCase):
    """Test lexer functionality"""

    queries = (
        # Basic keyword:value
        ("foo:bar",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar')]),
        ("foo: bar",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar')]),
        ("999: bar",
         [Token('WORD', '999'), Token(':', ':'), Token('WORD', 'bar')]),
        ("999C5: bar",
         [Token('WORD', '999C5'), Token(':', ':'), Token('WORD', 'bar')]),
        ("999__u: bar",
         [Token('WORD', '999__u'), Token(':', ':'), Token('WORD', 'bar')]),

        # Quoted strings
        ("foo: 'bar'",
         [Token('WORD', 'foo'), Token(':', ':'), Token('SIMPLE_QUOTED_STRING', "'bar'")]),
        ("foo: \"bar\"",
         [Token('WORD', 'foo'), Token(':', ':'), Token('DOUBLE_QUOTED_STRING', '"bar"')]),
        ("foo: /bar/",
         [Token('WORD', 'foo'), Token(':', ':'), Token('RE_STRING', '/bar/')]),
        ("foo: \"'bar'\"",
         [Token('WORD', 'foo'), Token(':', ':'), Token('DOUBLE_QUOTED_STRING', '"\'bar\'"')]),
        ('author:"Ellis, J"',
         [Token('WORD', 'author'), Token(':', ':'), Token('DOUBLE_QUOTED_STRING', '"Ellis, J"')]),

        # Date Range queries
        ("year: 2000->2012",
         [Token('WORD', 'year'), Token(':', ':'), Token('WORD', '2000'), Token('->', '->'), Token('WORD', '2012')]),
        ("year: 2000-10->2012-09",
         [Token('WORD', 'year'), Token(':', ':'), Token('WORD', '2000'),
          Token('-', '-'), Token('WORD', '10'), Token('->', '->'),
          Token('WORD', '2012'), Token('-', '-'), Token('WORD', '09')]),
        ("year: 2000-10 -> 2012-09",
         [Token('WORD', 'year'), Token(':', ':'), Token('WORD', '2000'),
          Token('-', '-'), Token('WORD', '10'), Token('->', '->'),
          Token('WORD', '2012'), Token('-', '-'), Token('WORD', '09')]),

        # Star patterns
        ("foo: hello*",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'hello'), Token('*', '*')]),
        ("foo: 'hello*'",
         [Token('WORD', 'foo'), Token(':', ':'), Token('SIMPLE_QUOTED_STRING', "'hello*'")]),
        ("foo: \"hello*\"",
         [Token('WORD', 'foo'), Token(':', ':'), Token('DOUBLE_QUOTED_STRING', '"hello*"')]),
        ("foo: he*o",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'he'), Token('*', '*'), Token('WORD', 'o')]),
        ("foo: he*lo",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'he'), Token('*', '*'), Token('WORD', 'lo')]),
        ("foo: he*lo*",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'he'), Token('*', '*'), Token('WORD', 'lo'), Token('*', '*')]),
        ("foo: *hello",
         [Token('WORD', 'foo'), Token(':', ':'), Token('*', '*'), Token('WORD', 'hello')]),

        # O'Shea
        ("foo: O'Shea",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'O'), Token('XWORD', "'"), Token('WORD', 'Shea')]),

        # Unicode characters
        ("foo: пушкин",
         [Token('WORD', 'foo'), Token(':', ':'), Token('XWORD', 'пушкин')]),
        ("foo: Lemaître",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'Lema'), Token('XWORD', 'î'), Token('WORD', 'tre')]),
        ('foo: "Lemaître"',
         [Token('WORD', 'foo'), Token(':', ':'), Token('DOUBLE_QUOTED_STRING', '"Lemaître"')]),
        ("refersto:hep-th/0201100",
         [Token('WORD', 'refersto'), Token(':', ':'), Token('WORD', 'hep'),
          Token('-', '-'), Token('WORD', 'th'), Token('XWORD', '/'),
          Token('WORD', '0201100')]),

        # Combined queries
        ("foo:bar foo:bar",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar')]),
        ("foo:bar and foo:bar",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token('AND', 'and'), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar')]),
        ("foo:bar AND foo:bar",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token('AND', 'AND'), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar')]),
        ("foo:bar or foo:bar",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token('OR', 'or'), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar')]),
        ("foo:bar | foo:bar",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token('|', '|'), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar')]),
        ("foo:bar not foo:bar",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token('NOT', 'not'), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar')]),
        ("foo:bar -foo:bar",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token('-', '-'), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar')]),
        ("((foo:bar))",
         [Token('(', '('), Token('(', '('), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token(')', ')'), Token(')', ')')]),
        ("(foo:bar)",
         [Token('(', '('), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token(')', ')')]),
        ("(foo:bar) or foo:bar",
         [Token('(', '('), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token(')', ')'), Token('OR', 'or'), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar')]),
        ("foo:bar or (foo:bar)",
         [Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token('OR', 'or'), Token('(', '('), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token(')', ')')]),
        ("(foo:bar) or (foo:bar)",
         [Token('(', '('), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token(')', ')'), Token('OR', 'or'), Token('(', '('), Token('WORD', 'foo'), Token(':', ':'), Token('WORD', 'bar'), Token(')', ')')]),

        # Simple spires syntax
        ("find t quark",
         [Token('FIND', 'find'), Token('WORD', 't'), Token('WORD', 'quark')]),
        ("find a richter, b",
         [Token('FIND', 'find'), Token('WORD', 'a'), Token('WORD', 'richter'), Token('XWORD', ','), Token('WORD', 'b')]),
        ("find date > 1984",
         [Token('FIND', 'find'), Token('WORD', 'date'), Token('>', '>'), Token('WORD', '1984')]),
        ("find date before 1984",
         [Token('FIND', 'find'), Token('WORD', 'date'), Token('BEFORE', 'before'), Token('WORD', '1984')]),
        ("find date after 1984",
         [Token('FIND', 'find'), Token('WORD', 'date'), Token('AFTER', 'after'), Token('WORD', '1984')]),
        ("find 1984->2000",
         [Token('FIND', 'find'), Token('WORD', '1984'), Token('->', '->'), Token('WORD', '2000')]),
        ("find 1984-01->2000-01",
         [Token('FIND', 'find'), Token('WORD', '1984'), Token('-', '-'), Token('WORD', '01'), Token('->', '->'), Token('WORD', '2000'), Token('-', '-'), Token('WORD', '01')]),
        ("find j phys.rev.,D50,1140",
         [Token('FIND', 'find'), Token('WORD', 'j'), Token('WORD', 'phys'), Token('XWORD', '.'), Token('WORD', 'rev'), Token('XWORD', '.,'), Token('WORD', 'D50'), Token('XWORD', ','), Token('WORD', '1140')]),
        ("find eprint arxiv:1007.5048",
         [Token('FIND', 'find'), Token('WORD', 'eprint'), Token('WORD', 'arxiv'), Token(':', ':'), Token('WORD', '1007'), Token('XWORD', '.'), Token('WORD', '5048')]),
        ('find fulltext "quark-gluon plasma"',
         [Token('FIND', 'find'), Token('WORD', 'fulltext'), Token('DOUBLE_QUOTED_STRING', '"quark-gluon plasma"')]),
        ('find topcite 200+',
         [Token('FIND', 'find'), Token('WORD', 'topcite'), Token('WORD', '200'), Token('+', '+')]),
        ("FIND t quark",
         [Token('FIND', 'FIND'), Token('WORD', 't'), Token('WORD', 'quark')]),
        ("fin t quark",
         [Token('FIND', 'fin'), Token('WORD', 't'), Token('WORD', 'quark')]),
        ("f t quark",
         [Token('FIND', 'f'), Token('WORD', 't'), Token('WORD', 'quark')]),
        ("find a richter, b and t quark and date > 1984",
         [Token('FIND', 'find'), Token('WORD', 'a'), Token('WORD', 'richter'), Token('XWORD', ','), Token('WORD', 'b'), Token('AND', 'and'), Token('WORD', 't'), Token('WORD', 'quark'), Token('AND', 'and'), Token('WORD', 'date'), Token('>', '>'), Token('WORD', '1984')]),
    )


@generate_tests(generate_parser_test)  # pylint: disable=R0903
class TestParser(InvenioTestCase):
    """Test parser functionality"""

    queries = ()


TEST_SUITE = make_test_suite(TestLexer, TestParser)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
