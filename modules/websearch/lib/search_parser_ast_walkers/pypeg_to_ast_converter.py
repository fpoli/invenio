# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

from invenio.visitor import make_visitor

from invenio import search_engine_spires_ast as ast
from invenio import search_engine_spires_parser as parser


class PypegConverter(object):
    visitor = make_visitor()

    # pylint: disable=W0613,E0102

    @visitor(parser.Whitespace)
    def visit(self, node):
        return ast.Value(node.value)

    @visitor(parser.Not)
    def visit(self, node, child):
        return ast.NotOp(child)

    @visitor(parser.And)
    def visit(self, node, left, right):
        return ast.AndOp(left, right)

    @visitor(parser.Or)
    def visit(self, node, left, right):
        return ast.Or(left, right)

    @visitor(parser.Word)
    def visit(self, node):
        return ast.Keyword(node.value)

    @visitor(parser.SingleQuotedString)
    def visit(self, node):
        return ast.SingleQuotedValue(node.value)

    @visitor(parser.DoubleQuotedString)
    def visit(self, node):
        return ast.DoubleQuotedValue(node.value)

    @visitor(parser.SlashQuotedString)
    def visit(self, node):
        return ast.RegexValue(node.value)

    @visitor(parser.SimpleValue)
    def visit(self, node):
        return ast.Value(node.value)

    @visitor(parser.SimpleRangeValue)
    def visit(self, node):
        return ast.Value(node.value)

    @visitor(parser.RangeValue)
    def visit(self, node, child):
        return child

    @visitor(parser.RangeOp)
    def visit(self, node, left, right):
        return ast.RangeOp(left, right)

    @visitor(parser.Value)
    def visit(self, node, child):
        return child

    @visitor(parser.SimpleSpiresValue)
    def visit(self, node, children):
        return ast.Value("".join([c.value for c in children]))

    @visitor(parser.SpiresValue)
    def visit(self, node, children):
        return ast.Value("".join([c.value for c in children]))

    @visitor(parser.SpiresSimpleQuery)
    def visit(self, node, keyword, value):
        return ast.SpiresOp(keyword, value)

    @visitor(parser.SpiresNotQuery)
    def visit(self, node, child):
        return ast.NotOp(child)

    @visitor(parser.SpiresParenthesizedQuery)
    def visit(self, node, child):
        return child

    @visitor(parser.SpiresAndQuery)
    def visit(self, node, left, right):
        return ast.AndOp(left, right)

    @visitor(parser.SpiresOrQuery)
    def visit(self, node, left, right):
        return ast.NotOp(left, right)

    @visitor(parser.SpiresQuery)
    def visit(self, node, child):
        return child

    @visitor(parser.ValueQuery)
    def visit(self, node, child):
        return ast.ValueQuery(child)

    @visitor(parser.KeywordQuery)
    def visit(self, node, keyword, value):
        return ast.KeywordOp(keyword, value)

    @visitor(parser.SimpleQuery)
    def visit(self, node, child):
        return child

    @visitor(parser.NotQuery)
    def visit(self, node, child):
        return ast.NotOp(child)

    @visitor(parser.ParenthesizedQuery)
    def visit(self, node, child):
        return child

    @visitor(parser.AndQuery)
    def visit(self, node, left, right):
        return ast.AndOp(left, right)

    @visitor(parser.ImplicitAndQuery)
    def visit(self, node, left, right):
        return ast.AndOp(left, right)

    @visitor(parser.OrQuery)
    def visit(self, node, left, right):
        return ast.OrOp(left, right)

    @visitor(parser.Query)
    def visit(self, node, child):
        return child

    @visitor(parser.FindQuery)
    def visit(self, node, child):
        return child

    @visitor(parser.Main)
    def visit(self, node, child):
        return child

    # pylint: enable=W0612,E0102

plugin_class = PypegConverter