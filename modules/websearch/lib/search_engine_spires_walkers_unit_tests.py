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

from functools import partial

from invenio.testutils import (make_test_suite,
                               run_test_suite,
                               InvenioTestCase,
                               nottest)
from invenio.search_engine_spires_parser import (parseQuery,
                                                 lexQuery,
                                                 generate_lexer,
                                                 generate_parser)
from invenio.search_engine_spires_ast import (AndOp, KeywordOp, OrOp,
                                              NotOp, Keyword, Value,
                                              SingleQuotedValue, NotOp,
                                              DoubleQuotedValue,
                                              RegexValue, RangeOp, SpiresOp)
from invenio.search_engine_spires_parser import load_walkers
from invenio.search_engine_spires_parser_unit_tests import generate_tests
from rply import ParsingError


@nottest
def generate_walker_test(query, expected):
    def func(self):
        try:
            tree = parseQuery(query)
        except ParsingError as e:
            print 'Source pos', e.getsourcepos()
            raise
        else:
            new_tree = tree.accept(self.walker())
            self.assertEqual(new_tree, expected)
    return func


@generate_tests(generate_walker_test)  # pylint: disable=R0903
class TestSpiresToInvenio(InvenioTestCase):
    """Test parser functionality"""

    queries = (
        ("find t quark",
         KeywordOp(Keyword('t'), Value('quark'))),
    )

    @classmethod
    def setUpClass(cls):
        cls.walker = load_walkers()['spires_to_invenio_converter']


TEST_SUITE = make_test_suite(TestSpiresToInvenio)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
