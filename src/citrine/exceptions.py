"""Citrine-specific exceptions."""
from typing import Optional, List
from uuid import UUID

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
        self.url = path
        self.detailed_error_info = []
        if response is not None:
            self.response_text = response.text
            self.code = response.status_code

            method = "unknown"
            if response.request is not None:
                method = response.request.method

            self.detailed_error_info.append(
                "{} (code: {}) returned from {} request to path: '{}'".format(
                    response.reason, self.code, method, path
                )
            )
            try:
                resp_json = response.json()
                if isinstance(resp_json, dict):
                    from citrine.resources.api_error import ApiError
                    self.api_error = ApiError.from_dict(resp_json)

                    validation_error_msgs = [
                        "{} ({})".format(f.failure_message, f.failure_id)
                        for f in self.api_error.validation_errors]

                    if self.api_error.message is not None:
                        self.detailed_error_info.append(self.api_error.message)
                    self.detailed_error_info.extend(validation_error_msgs)
                else:
                    self.api_error = None
                    if response.text is not None:
                        self.detailed_error_info.append(response.text)
            except (TypeError, ValueError):
                # If the response does not have a json dictionary, use its text
                self.api_error = None
                if response.text is not None:
                    self.detailed_error_info.append(response.text)
        else:
            self.http_err = path
            self.response_text = None
            self.code = None
            self.api_error = None

        super().__init__("\n\t".join(self.detailed_error_info))


class NotFound(NonRetryableHttpException):
    """A particular url was not found. (http status 404)."""

    pass


class Unauthorized(NonRetryableHttpException):
    """The user is unauthorized to make this api call. (http status 401)."""

    pass


class BadRequest(NonRetryableHttpException):
    """The user is trying to perform an invalid operation. (http status 400)."""

    pass


class WorkflowConflictException(NonRetryableHttpException):
    """There is a conflict preventing the workflow from being executed. (http status 409)."""

    pass


# A 409 is a Conflict, and can be raised anywhere a conflict occurs, not just in a workflow.
Conflict = WorkflowConflictException


class WorkflowNotReadyException(RetryableException):
    """The workflow is not ready to be executed. I.e., still validating. (http status 425)."""

    pass


class PollingTimeoutError(NonRetryableException):
    """Polling for an asynchronous result has exceeded the timeout."""

    pass


class JobFailureError(NonRetryableException):
    """The asynchronous job completed with the given failure message."""

    def __init__(self, *, message: str, job_id: UUID, failure_reasons: List[str]):
        super().__init__(message)
        self.job_id = job_id
        self.failure_reasons = failure_reasons


class ModuleRegistrationFailedException(NonRetryableException):
    """A module failed to register."""

    def __init__(self, moduleType: str, exc: Exception):
        err = 'The "{0}" failed to register. {1}: {2}'.format(
            moduleType, exc.__class__.__name__, str(exc))
        super().__init__(err)
