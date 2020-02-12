"""Test dependencies library upgrade script."""
from textwrap import dedent

import pytest
from click.testing import CliRunner

from dependencies_upgrade import main


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
        from rest_framework.viewsets import ModelViewSet
 
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
        from dependencies.contrib.rest_framework import model_view_set
         
        @model_view_set
        class SubscriptionsViewSet(Injector):
            serializer_class = SubscriptionSerializer
        """
    )

    after = dedent(
        """
        from stories import story, Success

        class Action:
            @story
            def do(I):
                I.one

            def one(self, ctx):
                ctx.foo = 1
                return Success()
        """
    )

    f = tmpdir.join("f.py")
    f.write(before)

    runner = CliRunner()

    result = runner.invoke(main, [f.strpath])
    assert result.exit_code == 1
    assert result.output == f"Update {f.strpath}\n\n1 file updated\n"

    assert f.read() == after