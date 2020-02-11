"""
Upgrade imports and view classes with dependencies definitions to the new version of the library API.

"""
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
from typing import Tuple
from typing import Union

import click
from more_itertools import strip
from tokenize_rt import Offset
from tokenize_rt import reversed_enumerate
from tokenize_rt import src_to_tokens
from tokenize_rt import Token
from tokenize_rt import tokens_to_src


@click.command()
@click.argument(
    "filenames",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, writable=True
    ),
)
@click.pass_context
def main(ctx: click.Context, filenames: List[str]) -> None:
    """CLI entrypoint for dependencies_upgrade tool."""
    modified = 0
    for filename in filenames:
        with open(filename, "r") as f:
            source = f.read()
        output = _upgrade(source)
        if source != output:
            modified += 1
            click.echo(f"Update {click.format_filename(f.name)}")
            with open(filename, "w") as f:
                f.write(output)
    if modified:
        suffix = "s" if modified > 1 else ""
        click.echo(f"\n{modified} file{suffix} updated")
        ctx.exit(1)


def _upgrade(source: str) -> str:
    return source

