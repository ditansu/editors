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


@pytest.mark.parametrize("returned_class", ["Success", "Skip"])
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


@pytest.mark.parametrize("returned_class", ["Success", "Skip"])
def test_migrate_ctx_assignment(returned_class):
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
                return {returned_class}(foo=1)
        """
    ).format(returned_class=returned_class)

    after = dedent(
        """
        from stories import story, {returned_class}

        class Action:
            @story
            def do(I):
                I.one

            def one(self, ctx):
                ctx.foo = 1
                return {returned_class}()
        """
    ).format(returned_class=returned_class)

    assert _upgrade(before) == after


@pytest.mark.parametrize("returned_class", ["Success", "Skip"])
def test_migrate_ctx_multiple_assignment(returned_class):
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
                return {returned_class}(foo=1, bar=2)
        """
    ).format(returned_class=returned_class)

    after = dedent(
        """
        from stories import story, {returned_class}

        class Action:
            @story
            def do(I):
                I.one

            def one(self, ctx):
                ctx.foo = 1
                ctx.bar = 2
                return {returned_class}()
        """
    ).format(returned_class=returned_class)

    assert _upgrade(before) == after
