import re


def node_type(node):
    return node[0]


def node_ast(node):
    return node[1]


class Node(object):
    def __init__(self, _type, ast):
        self.type = _type
        self.ast = ast

    @classmethod
    def from_dict(cls, ast):
        return Node(node_type(ast), node_ast(ast))


# Stores the actual visitor methods
def make_visitor():
    _methods = {}

    # The actual @visitor decorator
    def _visitor(arg_type):
        """Decorator that creates a visitor method."""

        # Delegating visitor implementation
        def _visitor_impl(self, arg, *args, **kwargs):
            """Actual visitor method implementation."""
            method = _methods[arg.type]
            return method(self, arg.ast , *args, **kwargs)

        def decorator(fn):
            _methods[arg_type] = fn
            # Replace all decorated methods with _visitor_impl
            return _visitor_impl

        return decorator

    return _visitor


class TreeWalker(object):

    """
    The AST structure is created by pyPEG.
    """

    visitor = make_visitor()

    def walk_ast(self, ast):
        def visit_el(el):
            if isinstance(el, tuple):
                node = Node.from_dict(el)
                return self.visit(node)
            elif isinstance(el, str):
                return el
            else:
                raise Exception()
        return "".join(visit_el(el) for el in ast)



    @visitor(Query)
    def visit(self, ast):
        return "{#%s#}" % ast[2:-2]
