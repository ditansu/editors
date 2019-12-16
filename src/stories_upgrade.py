"""Upgrade classes with stories definitions to the new version of the library API."""
import ast
from itertools import dropwhile
from typing import List
from typing import Optional
from typing import Set
from typing import Union

from more_itertools import split_at
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
        self.ctx_returned: Set[Offset] = set()
        self.ctx_kwargs: Set[Offset] = set()

    def visit_Return(self, node: ast.Return) -> None:
        if self.is_success(node.value) or self.is_skip(node.value):
            self.ctx_returned.add(_ast_to_offset(node))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self.is_success(node) or self.is_skip(node):
            self.ctx_kwargs.add(_ast_to_offset(node.func))
        self.generic_visit(node)

    def is_success(self, node: Optional[ast.expr]) -> bool:
        return self.is_returned(node, "Success")

    def is_skip(self, node: Optional[ast.expr]) -> bool:
        return self.is_returned(node, "Skip")

    def is_returned(self, node: Optional[ast.expr], name: str) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == name
            and not node.args
        )


def _ast_to_offset(node: Union[ast.expr, ast.stmt]) -> Offset:
    return Offset(node.lineno, node.col_offset)


def _mutate_found(tokens: List[Token], visitor: _FindAssignment) -> None:
    for i, token in reversed_enumerate(tokens):
        if token.offset in visitor.ctx_kwargs:
            brace_start = i
            brace_end = _find_closing_brace(tokens, brace_start)
        elif token.offset in visitor.ctx_returned:
            return_start = i
            if not return_start < brace_start < brace_end:
                raise Exception
            inserted = _process_ctx_returned(
                tokens, return_start, brace_start, brace_end
            )
            _process_ctx_kwargs(tokens, brace_start + inserted, brace_end + inserted)


def _process_ctx_returned(
    tokens: List[Token], return_start: int, brace_start: int, brace_end: int
) -> int:
    inserted = 0
    offset = brace_start + 2
    limit = brace_end - 1
    kwargs = tokens[offset:limit]

    for assignment in reversed(list(split_at(kwargs, lambda token: token.src == ","))):
        key, value = list(split_at(assignment, lambda token: token.src == "="))
        name = next(filter(lambda token: token.name == "NAME", key))
        variable = list(dropwhile(lambda token: token.src.isspace(), value))
        patch = [
            Token(name="NAME", src="ctx"),
            Token(name="OP", src="."),
            name,
            Token(name="UNIMPORTANT_WS", src=" "),
            Token(name="OP", src="="),
            Token(name="UNIMPORTANT_WS", src=" "),
            *variable,
            Token(name="NEWLINE", src="\n"),
            tokens[return_start - 1],  # indent
        ]
        tokens[return_start:return_start] = patch
        inserted += len(patch)
    return inserted


def _process_ctx_kwargs(tokens: List[Token], brace_start: int, brace_end: int) -> None:
    offset = brace_start + 2
    limit = brace_end - 1
    del tokens[offset:limit]


def _find_closing_brace(tokens: List[Token], i: int) -> int:
    i += 2
    brace_stack = ["("]

    while brace_stack:
        token = tokens[i].src
        i += 1
        if token == BRACES[brace_stack[-1]]:
            brace_stack.pop()
        elif token in BRACES:
            brace_stack.append(token)

    return i


BRACES = {"(": ")", "[": "]", "{": "}"}
