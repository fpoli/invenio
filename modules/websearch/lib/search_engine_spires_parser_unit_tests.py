# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011, 2012, 2013 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the search engine query parsers."""

from invenio.testutils import (make_test_suite,
                               run_test_suite,
                               InvenioTestCase,
                               nottest)
from invenio.search_engine_spires_parser import (parseQuery,
                                                 load_walkers)
from invenio.search_engine_spires_ast import (AndOp, KeywordOp, OrOp,
                                              NotOp, Keyword, Value,
                                              SingleQuotedValue, NotOp,
                                              DoubleQuotedValue, ValueQuery,
                                              RegexValue, RangeOp, SpiresOp)


WALKERS = load_walkers()


@nottest
def generate_parser_test(query, expected):
    def func(self):
        tree = parseQuery(query)
        converter = WALKERS['pypeg_to_ast_converter']()
        tree = tree.accept(converter)
        printer = WALKERS['repr_printer']()
        print 'tree', tree.accept(printer)
        print 'expected', expected.accept(printer)
        self.assertEqual(tree, expected)
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


@generate_tests(generate_parser_test)  # pylint: disable=R0903
class TestParser(InvenioTestCase):

    """Test parser functionality"""

    queries = (
        ("bar",
          ValueQuery(Value('bar'))),
        ("J. Ellis",
         AndOp(ValueQuery(Value('J.')), ValueQuery(Value('Ellis')))),
        ("$e^{+}e^{-}$",
         ValueQuery(Value('$e^{+}e^{-}$'))),

        # Basic keyword:value
        ("foo:bar",
         KeywordOp(Keyword('foo'), Value('bar'))),
        ("foo: bar",
         KeywordOp(Keyword('foo'), Value('bar'))),
        ("999: bar",
         KeywordOp(Keyword('999'), Value('bar'))),
        ("999C5: bar",
         KeywordOp(Keyword('999C5'), Value('bar'))),
        ("999__u: bar",
         KeywordOp(Keyword('999__u'), Value('bar'))),
        ("  foo  :  bar  ",
         KeywordOp(Keyword('foo'), Value('bar'))),

        # Quoted strings
        ("foo: 'bar'",
         KeywordOp(Keyword('foo'), SingleQuotedValue('bar'))),
        ("foo: \"bar\"",
         KeywordOp(Keyword('foo'), DoubleQuotedValue('bar'))),
        ("foo: /bar/",
         KeywordOp(Keyword('foo'), RegexValue('bar'))),
        ("foo: \"'bar'\"",
         KeywordOp(Keyword('foo'), DoubleQuotedValue("'bar'"))),
        ('author:"Ellis, J"',
         KeywordOp(Keyword('author'), DoubleQuotedValue("Ellis, J"))),

        # Range queries
        ("year: 2000->2012",
         KeywordOp(Keyword('year'), RangeOp(Value('2000'), Value('2012')))),
        ("year: 2000-10->2012-09",
         KeywordOp(Keyword('year'), RangeOp(Value('2000-10'), Value('2012-09')))),
        ("cited: 3->30",
         KeywordOp(Keyword('cited'), RangeOp(Value('3'), Value('30')))),
        ('author: Albert->John',
         KeywordOp(Keyword('author'), RangeOp(Value('Albert'), Value('John')))),
        ('author: "Albert"->John',
         KeywordOp(Keyword('author'), RangeOp(DoubleQuotedValue('Albert'), Value('John')))),
        ('author: Albert->"John"',
         KeywordOp(Keyword('author'), RangeOp(Value('Albert'), DoubleQuotedValue('John')))),
        ('author: "Albert"->"John"',
         KeywordOp(Keyword('author'), RangeOp(DoubleQuotedValue('Albert'), DoubleQuotedValue('John')))),

        # Star patterns
        ("foo: hello*",
         KeywordOp(Keyword('foo'), Value('hello*'))),
        ("foo: 'hello*'",
         KeywordOp(Keyword('foo'), SingleQuotedValue('hello*'))),
        ("foo: \"hello*\"",
         KeywordOp(Keyword('foo'), DoubleQuotedValue('hello*'))),
        ("foo: he*o",
         KeywordOp(Keyword('foo'), Value('he*o'))),
        ("foo: he*lo*",
         KeywordOp(Keyword('foo'), Value('he*lo*'))),
        ("foo: *hello",
         KeywordOp(Keyword('foo'), Value('*hello'))),

        # Special characters in keyword:value
        ("foo: O'Shea",
         KeywordOp(Keyword('foo'), Value("O'Shea"))),
        ("foo: e(-)",
         KeywordOp(Keyword('foo'), Value('e(-)'))),
        ("foo: e(+)e(-)",
         KeywordOp(Keyword('foo'), Value('e(+)e(-)'))),
        ("title: Si-28(p(pol.),n(pol.))",
         KeywordOp(Keyword('title'), Value('Si-28(p(pol.),n(pol.))'))),

        # Unicode characters
        ("foo: пушкин",
         KeywordOp(Keyword('foo'), Value("пушкин"))),
        ("foo: Lemaître",
         KeywordOp(Keyword('foo'), Value("Lemaître"))),
        ('foo: "Lemaître"',
         KeywordOp(Keyword('foo'), DoubleQuotedValue("Lemaître"))),
        ("refersto:hep-th/0201100",
         KeywordOp(Keyword('refersto'), Value("hep-th/0201100"))),

        # Combined queries
        ("foo:bar foo:bar",
         AndOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("foo:bar and foo:bar",
         AndOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("foo:bar AND foo:bar",
         AndOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("foo:bar or foo:bar",
         OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("foo:bar | foo:bar",
         OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("foo:bar not foo:bar",
         AndOp(KeywordOp(Keyword('foo'), Value('bar')), NotOp(KeywordOp(Keyword('foo'), Value('bar'))))),
        ("foo:bar -foo:bar",
         AndOp(KeywordOp(Keyword('foo'), Value('bar')), NotOp(KeywordOp(Keyword('foo'), Value('bar'))))),
        ("foo:bar- foo:bar",
         AndOp(KeywordOp(Keyword('foo'), Value('bar-')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("(foo:bar)",
         KeywordOp(Keyword('foo'), Value('bar'))),
        ("((foo:bar))",
         KeywordOp(Keyword('foo'), Value('bar'))),
        ("(((foo:bar)))",
         KeywordOp(Keyword('foo'), Value('bar'))),
        ("(foo:bar) or foo:bar",
         OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("foo:bar or (foo:bar)",
         OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("(foo:bar) or (foo:bar)",
         OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("(foo:bar)or(foo:bar)",
         OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("(foo:bar)|(foo:bar)",
         OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("(foo:bar)| (foo:bar)",
         OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("( foo:bar) or ( foo:bar)",
         OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("(foo:bar) or (foo:bar )",
         OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
        ("foo:bar and foo:bar and foo:bar",
            AndOp(KeywordOp(Keyword('foo'), Value('bar')),
                  AndOp(KeywordOp(Keyword('foo'), Value('bar')),
                        KeywordOp(Keyword('foo'), Value('bar'))))),
        ("aaa +bbb -ccc +ddd",
         AndOp(ValueQuery(Value('aaa')),
               AndOp(ValueQuery(Value('bbb')),
                     NotOp(AndOp(ValueQuery(Value('ccc')),
                                 ValueQuery(Value('ddd'))
        ))))),

        # Second order keyword operation
        # TODO: Do we want a new AST node called 'NestedOp'?
        ("refersto:author:Ellis",
         KeywordOp(Keyword('refersto'), KeywordOp(Keyword('author'), Value('Ellis')))),
        ("refersto:refersto:author:Ellis",
         KeywordOp(Keyword('refersto'), KeywordOp(Keyword('refersto'), KeywordOp(Keyword('author'), Value('Ellis'))))),
        ("refersto:(foo:bar)",
         KeywordOp(Keyword('refersto'), KeywordOp(Keyword('foo'), Value('bar')))),
        ("refersto:(foo:bar and Ellis)",
         KeywordOp(Keyword('refersto'), AndOp(KeywordOp(Keyword('foo'), Value('bar')), ValueQuery(Value('Ellis'))))),

        # Spires syntax
        ("find t quark",
         SpiresOp(Keyword('t'), Value('quark'))),
        ("find a richter, b",
         SpiresOp(Keyword('a'), Value('richter, b'))),
        ("find a:richter, b a",
         SpiresOp(Keyword('a'), Value('richter, b a'))),
        ("find t quark   ",
         SpiresOp(Keyword('t'), Value('quark'))),
        ("   find t quark   ",
         SpiresOp(Keyword('t'), Value('quark'))),
        ("find t quark ellis  ",
         SpiresOp(Keyword('t'), Value('quark'))),
        ("find t quark and a ellis",
         AndOp(SpiresOp(Keyword('t'), Value('quark')), SpiresOp(Keyword('a'), Value('ellis')))),
        ("find t quark or a ellis",
         OrOp(SpiresOp(Keyword('t'), Value('quark')), SpiresOp(Keyword('a'), Value('ellis')))),
        ("find (t quark) or (a ellis)",
         OrOp(SpiresOp(Keyword('t'), Value('quark')), SpiresOp(Keyword('a'), Value('ellis')))),
        ("find (t quark or a ellis)",
         OrOp(SpiresOp(Keyword('t'), Value('quark')), SpiresOp(Keyword('a'), Value('ellis')))),
        ("find ((t quark) or (a ellis))",
         OrOp(SpiresOp(Keyword('t'), Value('quark')), SpiresOp(Keyword('a'), Value('ellis')))),
        ("find (( t quark )|( a ellis ))",
         OrOp(SpiresOp(Keyword('t'), Value('quark')), SpiresOp(Keyword('a'), Value('ellis')))),
        ("find (( t quark )|( a:ellis ))",
         OrOp(SpiresOp(Keyword('t'), Value('quark')), SpiresOp(Keyword('a'), Value('ellis')))),
        ("find a l everett or t light higgs and j phys.rev.lett. and primarch hep-ph",
         OrOp(SpiresOp(Keyword('a'), Value('l everett')),
              AndOp(SpiresOp(Keyword('t'), Value('light higgs')),
                    AndOp(SpiresOp(Keyword('j'), Value('phys.rev.lett.')),
                          SpiresOp(Keyword('primarch'), Value('hep-ph')))))),

        ("find texkey Allison:1980vw",
         SpiresOp(Keyword('texkey'), Value('Allison:1980vw'))),

        # TODO: create a GreaterOp
        # ("find date > 1984",
        #  SpiresOp(Keyword('date'), GreaterOp('1984')))
        # ("find date >= 1984",
        #  SpiresOp(Keyword('date'), GreaterEqualOp('1984')))
        # ("find topcite 200+",
        #  SpiresOp(Keyword('topcite'), GreaterEqualOp('200')))
        # ("find date <= 2014-10-01",
        #  SpiresOp(Keyword('date'), LessEqualOp('2014-10-01')))
        # ("find da today - 2",
        #  SpiresOp(Keyword('da'), Value('today - 2')))
        # ("find du > yesterday - 2",
        #  SpiresOp(Keyword('du'), GreaterOp('today - 2'))

        # This will be difficult without knowing the list of second-order keywords
        ("find refersto a ellis",
         SpiresOp(Keyword('refersto'), SpiresOp(Keyword('a'), Value('ellis')))),
        
    )

    # queries = (
    #     ("(foo:bar) or foo:bar",
    #      OrOp(KeywordOp(Keyword('foo'), Value('bar')), KeywordOp(Keyword('foo'), Value('bar')))),
    #            )

TEST_SUITE = make_test_suite(TestParser)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
