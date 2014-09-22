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

from invenio.search_engine_spires_ast import (AndOp, KeywordOp, OrOp,
                                              NotOp, Keyword, Value,
                                              SingleQuotedValue,
                                              DoubleQuotedValue,
                                              RegexValue, RangeOp, SpiresOp)


class SpiresToInvenio(object):
    visitor = make_visitor()

    # pylint: disable=W0613,E0102

    @visitor(AndOp)
    def visit(self, node, left, right):
        return type(node)(left, right)

    @visitor(OrOp)
    def visit(self, node, left, right):
        return type(node)(left, right)

    @visitor(KeywordOp)
    def visit(self, node, left, right):
        return type(node)(left, right)

    @visitor(RangeOp)
    def visit(self, node, left, right):
        return type(node)(left, right)

    @visitor(NotOp)
    def visit(self, node, op):
        return type(node)(op)

    @visitor(Keyword)
    def visit(self, node):
        return type(node)(node.value)

    @visitor(Value)
    def visit(self, node):
        return type(node)(node.value)

    @visitor(SingleQuotedValue)
    def visit(self, node):
        return type(node)(node.value)

    @visitor(DoubleQuotedValue)
    def visit(self, node):
        return type(node)(node.value)

    @visitor(RegexValue)
    def visit(self, node):
        return type(node)(node.value)

    @visitor(SpiresOp)
    def visit(self, node, left, right):
        # TODO: replace left spires keyword with invenio field
        return KeywordOp(left, right)

    # pylint: enable=W0612,E0102


plugin_class = SpiresToInvenio
