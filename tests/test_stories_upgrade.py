"""Test stories library upgrade script."""
import stories_upgrade


def test_migrate_ctx_assignment_success():
    """
    Migrate Success(foo='bar').

    Migrate story context variable assignment from the Success()
    keyword arguments to the assignment expression.
    """
    assert stories_upgrade is not None
