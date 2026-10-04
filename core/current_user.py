"""
Tracks the user acting in the current request or script, so audit fields
and history get filled without passing the user through every call.
"""
from contextlib import contextmanager
from contextvars import ContextVar

_current_user = ContextVar("current_user", default=None)


def get_current_user():
    """Return the authenticated user acting right now, or None."""
    user = _current_user.get()
    if user is None or not user.is_authenticated:
        return None
    return user


@contextmanager
def acting_as(user):
    """Run a block on behalf of a user (management commands, tasks, tests)."""
    token = _current_user.set(user)
    try:
        yield user
    finally:
        _current_user.reset(token)
