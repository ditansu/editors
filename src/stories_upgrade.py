"""Upgrade classes with stories definitions to the new version of the library API."""
import ast
from typing import List
from typing import Set
from typing import Union

from tokenize_rt import Offset
from tokenize_rt import reversed_enumerate
from tokenize_rt import src_to_tokens
from tokenize_rt import Token
from tokenize_rt import tokens_to_src


def _upgrade(source: str) -> str:
    ast_obj = _ast_parse(source)
    visitor = _FindAssignment()
    visitor.visit(ast_obj)
    tokens = src_to_tokens(source)
    _mutate_found(tokens, visitor)
    return tokens_to_src(tokens)


def _ast_parse(source: str) -> ast.Module:
    return ast.parse(source)


class _FindAssignment(ast.NodeVisitor):
    def __init__(self) -> None:
        self.ctx_kwargs: Set[Offset] = set()

    def visit_Call(self, node: ast.Call) -> None:
        if self.is_returned(node, "Success") or self.is_returned(node, "Skip"):
            self.ctx_kwargs.add(_ast_to_offset(node.func))
        self.generic_visit(node)

    def is_returned(self, node: ast.Call, name: str) -> bool:
        return (
            isinstance(node.func, ast.Name) and node.func.id == name and not node.args
        )


def _ast_to_offset(node: Union[ast.expr, ast.stmt]) -> Offset:
    return Offset(node.lineno, node.col_offset)


def _mutate_found(tokens: List[Token], visitor: _FindAssignment) -> None:
    for i, token in reversed_enumerate(tokens):
        if token.offset in visitor.ctx_kwargs:
            _process_ctx_kwargs(tokens, i)


def _process_ctx_kwargs(tokens: List[Token], start: int) -> None:
    i = offset = start + 2
    brace_stack = ["("]

    while brace_stack:
        token = tokens[i].src
        i += 1
        if token == BRACES[brace_stack[-1]]:
            brace_stack.pop()
        elif token in BRACES:
            brace_stack.append(token)

    limit = i - 1
    del tokens[offset:limit]


BRACES = {"(": ")", "[": "]", "{": "}"}
