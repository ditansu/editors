"""Test stories library upgrade script."""
from textwrap import dedent

import pytest
from click.testing import CliRunner

from stories_upgrade import _upgrade
from stories_upgrade import main


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
        from stories import story, Success

        class Action:
            @story
            def do(I):
                I.one

            def one(self, ctx):
                return Success()
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
        from stories import story, Success

        class Action:
            @story
            def do(I):
                I.one

            def one(self, ctx):
                return Success(foo=1)
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


@pytest.mark.parametrize("returned_class", ["Success", "Skip", "Failure", "Result"])
def test_migrate_empty_ctx(returned_class):
    """Don't modify methods without variable assignment in any case."""
    source = dedent(
        """
        from stories import story, {returned_class}

        class Action:
            @story
            def do(I):
                I.one

            def one(self, ctx):
                return {returned_class}()
        """
    ).format(returned_class=returned_class)

    assert _upgrade(source) == source


VALUES = ["1", "input()"]


@pytest.mark.parametrize("returned_class", ["Success", "Skip"])
@pytest.mark.parametrize("foo_value", VALUES)
def test_migrate_ctx_assignment(returned_class, foo_value):
    """
    Migrate Success(foo='bar').

    Migrate story context variable assignment from the Success()
    keyword arguments to the assignment expression.
    """
    before = dedent(
        """
        from stories import story, {returned_class}

        class Action:
            @story
            def do(I):
                I.one

            def one(self, ctx):
                return {returned_class}(foo={foo_value})
        """
    ).format(returned_class=returned_class, foo_value=foo_value)

    after = dedent(
        """
        from stories import story, {returned_class}

        class Action:
            @story
            def do(I):
                I.one

            def one(self, ctx):
                ctx.foo = {foo_value}
                return {returned_class}()
        """
    ).format(returned_class=returned_class, foo_value=foo_value)

    assert _upgrade(before) == after


@pytest.mark.parametrize("returned_class", ["Success", "Skip"])
@pytest.mark.parametrize("foo_value", VALUES)
@pytest.mark.parametrize("bar_value", VALUES)
def test_migrate_ctx_multiple_assignment(returned_class, foo_value, bar_value):
    """
    Migrate Success(foo='bar', baz='quiz').

    Migrate story context variable assignment from the Success()
    keyword arguments to the multiline assignment expression.
    """
    before = dedent(
        """
        from stories import story, {returned_class}

        class Action:
            @story
            def do(I):
                I.one

            def one(self, ctx):
                return {returned_class}(foo={foo_value}, bar={bar_value})
        """
    ).format(returned_class=returned_class, foo_value=foo_value, bar_value=bar_value)

    after = dedent(
        """
        from stories import story, {returned_class}

        class Action:
            @story
            def do(I):
                I.one

            def one(self, ctx):
                ctx.foo = {foo_value}
                ctx.bar = {bar_value}
                return {returned_class}()
        """
    ).format(returned_class=returned_class, foo_value=foo_value, bar_value=bar_value)

    assert _upgrade(before) == after
