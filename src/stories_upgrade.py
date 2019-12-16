"""Upgrade classes with stories definitions to the new version of the library API."""
import ast
from typing import cast
from typing import Dict
from typing import List
from typing import Optional
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
        self.ctx_returned: Dict[Offset, List[ast.keyword]] = {}
        self.ctx_kwargs: Set[Offset] = set()

    def visit_Return(self, node: ast.Return) -> None:
        if self.is_success(node.value) or self.is_skip(node.value):
            call = cast(ast.Call, node.value)
            self.ctx_returned[_ast_to_offset(node)] = call.keywords
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
        if token.offset in visitor.ctx_returned:
            _process_ctx_returned(tokens, i, visitor.ctx_returned[token.offset])
        elif token.offset in visitor.ctx_kwargs:
            _process_ctx_kwargs(tokens, i)


def _process_ctx_returned(
    tokens: List[Token], start: int, keywords: List[ast.keyword]
) -> None:
    tokens[start:start] = [
        Token(name="NAME", src="ctx"),
        Token(name="OP", src="."),
        Token(name="NAME", src="foo"),
        Token(name="UNIMPORTANT_WS", src=" "),
        Token(name="OP", src="="),
        Token(name="UNIMPORTANT_WS", src=" "),
        Token(name="NUMBER", src="1"),
        Token(name="NEWLINE", src="\n"),
        tokens[start - 1],  # indent
    ]


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
