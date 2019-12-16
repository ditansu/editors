"""Test stories library upgrade script."""
from textwrap import dedent

import pytest

from stories_upgrade import _upgrade


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
                return {returned_class}()
        """
    ).format(returned_class=returned_class)

    assert _upgrade(before) == after
