"""Citrine-specific exceptions."""


class CitrineException(Exception):
    """The base exception class for Citrine-Python exceptions."""

    pass


class NonRetryableException(CitrineException):
    """Indicates that a non-retryable error occurred."""

    pass


class RetryableException(CitrineException):
    """Indicates an error occurred but it is retryable."""

    pass


class UnauthorizedRefreshToken(NonRetryableException):
    """The token used to refresh authentication is invalid."""

    pass


class NotFound(NonRetryableException):
    """A particular url was not found. (http status 404)."""

    def __init__(self, path: str):
        super().__init__()
        self.url = path


class Unauthorized(NonRetryableException):
    """The user is unauthorized to make this api call. (http status 401)."""

    def __init__(self, path: str):
        super().__init__()
        self.url = path
