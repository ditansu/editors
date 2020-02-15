"""Test dependencies library upgrade script."""
from pprint import pprint
from textwrap import dedent

import pytest
from click.testing import CliRunner

from dependencies_upgrade import _upgrade
from dependencies_upgrade import main
from dependencies_upgrade import MIGRATE_IMPORT_FROM


def test_main():
    """Main entrypoint should return correct exit code."""
    runner = CliRunner()

    result = runner.invoke(main)
    assert result.exit_code == 0
    assert result.output == ""


def test_main_unchanged(tmpdir):
    """Main entrypoint should exit silently in no files changed."""
    source = dedent(
        """
        from foo.bar import baz
        from zzz import x as g

        class SubscriptionsViewSet(ModelViewSet):
            serializer_class = SubscriptionSerializer
        """
    )

    f = tmpdir.join("f.py")
    f.write(source)

    runner = CliRunner()

    result = runner.invoke(main, [f.strpath])
    assert result.exit_code == 0
    assert result.output == ""

    assert f.read() == source


def test_main_changed(tmpdir):
    """Main entrypoint should change files."""
    before = dedent(
        """
        # ViewSets.

        from foo import bar
        from {path} import {module}

        class SubscriptionsViewSet:
            pass
        """
    ).format(path="dependencies.contrib.rest_framework", module="model_view_set")

    after = dedent(
        """
        # ViewSets.

        from foo import bar
        from {path} import {module}

        class SubscriptionsViewSet:
            pass
        """
    ).format(path="rest_framework.viewsets", module="ModelViewSet")

    f = tmpdir.join("f.py")
    f.write(before)

    runner = CliRunner()

    result = runner.invoke(main, [f.strpath])
    assert result.exit_code == 1
    assert result.output == f"Update {f.strpath}\n\n1 file updated\n"

    assert f.read() == after


@pytest.mark.parametrize("old_import, expected_import", MIGRATE_IMPORT_FROM.items())
def test_migrate_import_from(old_import, expected_import):
    """
    Migrate from a contrib modules to framework native
    """

    before = dedent(
        """
        # ViewSets.

        from foo import bar
        from {path} import {module}

        class SubscriptionsViewSet:
            pass
        """
    ).format(path=old_import[0], module=old_import[1])

    after = dedent(
        """
        # ViewSets.

        from foo import bar
        from {path} import {module}

        class SubscriptionsViewSet:
            pass
        """
    ).format(path=expected_import[0], module=expected_import[1])

    upgraded = _upgrade(before)
    pprint(after)
    pprint(upgraded)
    assert upgraded == after
