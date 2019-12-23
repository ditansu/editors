"""Upgrade classes with stories definitions to the new version of the library API."""
import ast
from dataclasses import dataclass
from dataclasses import field
from itertools import dropwhile
from itertools import islice
from itertools import takewhile
from typing import cast
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import TextIO
from typing import Union

import click
from more_itertools import strip
from tokenize_rt import Offset
from tokenize_rt import reversed_enumerate
from tokenize_rt import src_to_tokens
from tokenize_rt import Token
from tokenize_rt import tokens_to_src


@click.command()
@click.argument("files", nargs=-1, type=click.File("r+"))
@click.pass_context
def main(ctx: click.Context, files: List[TextIO]) -> None:
    """CLI entrypoint for stories upgrade tool."""
    modified = 0
    for f in files:
        source = f.read()
        output = _upgrade(source)
        if source != output:
            modified += 1
            click.echo(f"Update {click.format_filename(f.name)}")
            f.seek(0)
            f.write(output)
    if modified:
        suffix = "s" if modified > 1 else ""
        click.echo(f"\n{modified} file{suffix} updated")
        ctx.exit(1)


def _upgrade(source: str) -> str:
    ast_obj = _ast_parse(source)
    visitor = _FindAssignment()
    visitor.visit(ast_obj)
    tokens = src_to_tokens(source)
    _mutate_found(tokens, visitor)
    return tokens_to_src(tokens)


def _ast_parse(source: str) -> ast.Module:
    return ast.parse(source)


@dataclass
class _FindAssignment(ast.NodeVisitor):
    ctx_returned: Set[Offset] = field(default_factory=set)
    ctx_kwargs: Set[Offset] = field(default_factory=set)

    def visit_Return(self, node: ast.Return) -> None:
        if self.is_success(node.value) or self.is_skip(node.value):
            call = cast(ast.Call, node.value)
            if call.keywords:
                self.ctx_returned.add(_ast_to_offset(node))
                self.ctx_kwargs.add(_ast_to_offset(call.func))
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
            brace_start = i + 1
            brace_end = _find_closing_brace(tokens, brace_start, "(")
            visitor.ctx_kwargs.remove(token.offset)
        elif token.offset in visitor.ctx_returned:
            return_start = i
            if not return_start < brace_start < brace_end:  # pragma: no cover
                raise Exception
            inserted = _process_ctx_returned(
                tokens, return_start, brace_start, brace_end
            )
            _process_ctx_kwargs(tokens, brace_start + inserted, brace_end + inserted)
            visitor.ctx_returned.remove(token.offset)


def _process_ctx_returned(
    tokens: List[Token], return_start: int, brace_start: int, brace_end: int
) -> int:
    inserted = 0
    offset = brace_start + 1
    limit = brace_end - 1
    kwargs = tokens[offset:limit]
    indent = tokens[return_start].utf8_byte_offset

    for assignment in reversed(list(_split_assign(kwargs))):
        key = takewhile(lambda token: token.src != "=", assignment)
        value = dropwhile(lambda token: token.src != "=", assignment)
        name = list(strip(key, lambda token: token.src.isspace()))
        variable = list(
            strip(islice(value, 1, None), lambda token: token.src.isspace())
        )
        patch = [
            Token(name="NAME", src="ctx"),
            Token(name="OP", src="."),
            *name,
            Token(name="UNIMPORTANT_WS", src=" "),
            Token(name="OP", src="="),
            Token(name="UNIMPORTANT_WS", src=" "),
            *variable,
            Token(name="NEWLINE", src="\n"),
            Token(name="INDENT", src=" " * indent),
        ]
        tokens[return_start:return_start] = patch
        inserted += len(patch)
    return inserted


def _process_ctx_kwargs(tokens: List[Token], brace_start: int, brace_end: int) -> None:
    offset = brace_start + 1
    limit = brace_end - 1
    del tokens[offset:limit]


def _find_closing_brace(tokens: List[Token], i: int, opening: str) -> int:
    if opening not in BRACES:
        raise Exception  # pragma: no cover
    j = i + 1
    brace_stack = [opening]

    while brace_stack:
        token = tokens[j].src
        j += 1
        if token == BRACES[brace_stack[-1]]:
            brace_stack.pop()
        elif token in BRACES:
            brace_stack.append(token)

    return j


BRACES = {"(": ")", "[": "]", "{": "}"}


def _split_assign(kwargs: List[Token]) -> Iterable[List[Token]]:
    chunk = []
    skip_until: Optional[int] = None
    for i, token in enumerate(kwargs):
        if skip_until is not None and i < skip_until - 1:
            continue
        elif skip_until is not None:
            skip_until = None
        elif token.src in BRACES:
            closing = _find_closing_brace(kwargs, i, token.src)
            chunk.extend(kwargs[i:closing])
            skip_until = closing
        elif token.src == ",":
            yield chunk
            chunk = []
        else:
            chunk.append(token)
    if not _all_whitespace(chunk):
        yield chunk


def _all_whitespace(tokens: List[Token]) -> bool:
    return all(token.src.isspace() for token in tokens)
