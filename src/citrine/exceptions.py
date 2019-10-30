"""Citrine-specific exceptions."""
from typing import Optional

from requests import Response


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


class NonRetryableHttpException(NonRetryableException):
    """An exception originating from an HTTP error from a Citrine API."""

    def __init__(self, path: str, response: Optional[Response] = None):
        super().__init__(path)
        self.url = path
        if response is not None:
            self.response_text = response.text
            self.code = response.status_code
            try:
                resp_json = response.json()
                if isinstance(resp_json, dict):
                    from citrine.resources.api_error import ApiError
                    self.api_error = ApiError.from_dict(resp_json)
                else:
                    self.api_error = None
            # TODO: throw specific exception in DictSerializable when deserialization
            #  fails due to from JSON keys
            except (TypeError, ValueError):
                self.api_error = None
        else:
            self.response_text = None
            self.code = None
            self.api_error = None


class NotFound(NonRetryableHttpException):
    """A particular url was not found. (http status 404)."""

    pass


class Unauthorized(NonRetryableHttpException):
    """The user is unauthorized to make this api call. (http status 401)."""

    pass


class BadRequest(NonRetryableHttpException):
    """The user is trying to perform an invalid operation. (http status 400)."""

    pass


class WorkflowConflictException(NonRetryableException):
    """There is a conflict preventing the workflow from being executed. (http status 409)."""

    pass


class WorkflowNotReadyException(RetryableException):
    """The workflow is not ready to be executed. i.e. still validating. (http status 425)."""

    pass


class ModuleRegistrationFailedException(NonRetryableException):
    """A module failed to register."""

    def __init__(self, moduleType: str, exc: Exception):
        err = 'The "{0}" failed to register. {1}: {2}'.format(
            moduleType, exc.__class__.__name__, str(exc))
        super().__init__(err)
