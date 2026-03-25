"""Tests for the Citrine exception hierarchy."""
import pytest

from citrine.exceptions import (
    BadRequest, CitrineException, NonRetryableException, NotFound,
    ServerError, Unauthorized, WorkflowConflictException,
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


# --- ServerError tests ---

def test_server_error_attributes():
    exc = ServerError(
        method="POST", path="/api/v1/foo",
        status_code=502, response_text="Bad Gateway",
        request_id="abc-123"
    )
    assert exc.method == "POST"
    assert exc.path == "/api/v1/foo"
    assert exc.status_code == 502
    assert exc.response_text == "Bad Gateway"
    assert exc.request_id == "abc-123"


def test_server_error_message_includes_context():
    exc = ServerError(
        method="GET", path="/api/v1/bar",
        status_code=500, response_text="internal error"
    )
    msg = str(exc)
    assert "500" in msg
    assert "GET" in msg
    assert "/api/v1/bar" in msg
    assert "internal error" in msg


def test_server_error_includes_request_id_in_message():
    exc = ServerError(
        method="PUT", path="/x",
        status_code=503, response_text="",
        request_id="req-456"
    )
    msg = str(exc)
    assert "req-456" in msg


def test_server_error_truncates_long_response():
    long_text = "x" * 1000
    exc = ServerError(
        method="GET", path="/",
        status_code=500, response_text=long_text
    )
    assert len(exc.response_text) == 500


def test_server_error_has_hint():
    exc = ServerError(
        method="GET", path="/",
        status_code=500, response_text="err"
    )
    assert exc.hint is not None
    assert "server-side" in exc.hint.lower()


def test_server_error_is_non_retryable():
    exc = ServerError(
        method="GET", path="/",
        status_code=500, response_text=""
    )
    assert isinstance(exc, NonRetryableException)


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
