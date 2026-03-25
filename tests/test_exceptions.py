"""Tests for the Citrine exception hierarchy."""
import pytest

from citrine.exceptions import (
    BadRequest, CitrineException, NotFound,
    Unauthorized, WorkflowConflictException,
)


def test_citrine_exception_without_hint():
    exc = CitrineException("something went wrong")
    assert str(exc) == "something went wrong"
    assert exc.hint is None


def test_citrine_exception_with_hint():
    exc = CitrineException("bad request", hint="Check your input.")
    assert "bad request" in str(exc)
    assert "Hint: Check your input." in str(exc)
    assert exc.hint == "Check your input."


def test_citrine_exception_hint_format():
    exc = CitrineException("error", hint="Try again.")
    expected = "error\n\nHint: Try again."
    assert str(exc) == expected


def test_citrine_exception_no_args():
    exc = CitrineException()
    assert str(exc) == ""
    assert exc.hint is None


def test_citrine_exception_no_args_with_hint():
    exc = CitrineException(hint="Do something.")
    assert "Hint: Do something." in str(exc)


def test_citrine_exception_is_catchable_as_exception():
    with pytest.raises(Exception):
        raise CitrineException("test")


def test_hint_preserved_through_subclass():
    """Subclasses that call super().__init__ with hint should work."""
    class MyError(CitrineException):
        pass

    exc = MyError("oops", hint="Fix it.")
    assert exc.hint == "Fix it."
    assert "Hint: Fix it." in str(exc)


# --- Default hint tests for HTTP exception subclasses ---

def test_not_found_has_default_hint():
    exc = NotFound("/test/path")
    assert exc.hint is not None
    assert "UID" in exc.hint


def test_unauthorized_has_default_hint():
    exc = Unauthorized("/test/path")
    assert exc.hint is not None
    assert "API key" in exc.hint


def test_bad_request_has_default_hint():
    exc = BadRequest("/test/path")
    assert exc.hint is not None
    assert "validation" in exc.hint.lower()


def test_conflict_has_default_hint():
    exc = WorkflowConflictException("/test/path")
    assert exc.hint is not None
    assert "retry" in exc.hint.lower()
