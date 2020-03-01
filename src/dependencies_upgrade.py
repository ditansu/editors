"""
Upgrade imports and view classes with dependencies definitions to the new version of the library API.

"""
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import click
from redbaron import RedBaron

ImportTuple = Tuple[str, str]
MigrateFromImportDict = Dict[ImportTuple, ImportTuple]

MIGRATE_FROM_IMPORT: MigrateFromImportDict = {
    ("dependencies.contrib.rest_framework", "model_view_set"): (
        "rest_framework.viewsets",
        "ModelViewSet",
    )
}


MIGRATE_DRF_CLASS_INJECTOR: Dict[str, str] = dict(model_view_set="ModelViewSet")


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
    code = _migrate_from_import(source=source, migrate_map=MIGRATE_FROM_IMPORT)
    code = _migrate_drf_class_injector(
        source=code, migrate_map=MIGRATE_DRF_CLASS_INJECTOR
    )
    return code


def _migrate_from_import(source: str, migrate_map: MigrateFromImportDict) -> str:
    import_idx = 0
    module_idx = 1
    node_name = "FromImportNode"
    red = RedBaron(source)
    for old, new in migrate_map.items():
        node = red.find(
            node_name,
            lambda x: x.value.dumps() == old[import_idx]
            and x.targets.dumps() == old[module_idx],
        )
        if node is None:
            continue
        node.value = new[import_idx]
        node.targets = new[module_idx]

    return red.dumps()


def _migrate_drf_class_injector(source: str, migrate_map: Dict[str, str]) -> str:
    node_name = "ClassNode"
    inherit_from = "Injector"

    red = RedBaron(source)
    for old, new in migrate_map.items():
        node = red.find(
            node_name,
            lambda x: x.inherit_from.dumps() == inherit_from
            and old in x.decorators.dumps(),
        )
        if node is None:
            continue

        # delete decorator
        decorator = next(dec for dec in node.decorators if dec.dumps() == f"@{old}")
        del node.decorators[decorator.index_on_parent]

        # replace injector
        injector = next(inj for inj in node.inherit_from if inj.dumps() == inherit_from)
        injector.value = new

    return red.dumps()
