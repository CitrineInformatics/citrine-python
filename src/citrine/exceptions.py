"""Exception hierarchy for the Citrine Python SDK.

All Citrine-specific exceptions inherit from :class:`CitrineException`.
Exceptions are divided into two categories:

* **Non-retryable** — the request will fail again if retried without
  changes (e.g., bad input, missing resource, auth failure).
* **Retryable** — the request may succeed on a subsequent attempt
  (e.g., server temporarily unavailable, workflow still validating).

HTTP-specific exceptions inherit from
:class:`NonRetryableHttpException` and carry the status code,
response body, and parsed API error details (when available).

"""
from types import SimpleNamespace
from typing import Optional, List
from urllib.parse import urlencode
from uuid import UUID

from requests import Response


class CitrineException(Exception):
    """Base exception for all Citrine SDK errors.

    All exceptions raised by this library inherit from this
    class, so ``except CitrineException`` will catch any
    Citrine-specific error.

    """

    pass


class NonRetryableException(CitrineException):
    """An error that will not succeed if the same request is retried.

    Common causes include invalid input, missing resources, or
    insufficient permissions. Fix the underlying issue before
    retrying.

    """

    pass


class RetryableException(CitrineException):
    """An error that may succeed if the request is retried later.

    The server returned a transient error. Callers can safely
    retry the request after a short delay.

    """

    pass


class UnauthorizedRefreshToken(NonRetryableException):
    """The API key used to refresh authentication is invalid.

    This typically means the API key has expired or been
    revoked. Generate a new key from the platform's account
    settings page.

    """

    pass


class NonRetryableHttpException(NonRetryableException):
    """An HTTP error response from the Citrine Platform API.

    Attributes
    ----------
    url : str
        The API path that was requested.
    code : int or None
        The HTTP status code (e.g. 400, 404).
    response_text : str or None
        The raw response body.
    api_error : ApiError or None
        Parsed error details including validation errors,
        if the response contained a JSON error body.
    detailed_error_info : list[str]
        Human-readable error lines joined in ``str(exc)``.

    """

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
                    self.api_error = ApiError.build(resp_json)

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
    """The requested resource was not found (HTTP 404).

    Verify that the resource UID is correct and that it
    exists in the expected project or dataset.

    """

    @staticmethod
    def build(*, message: str, method: str, path: str, params: dict = {}):
        """
        Construct a NotFound response from parameters.

        This allows raising NotFound locally to produce consistent behavior even if the server
        doesn't return a 404.

        Parameters
        ----------
        message: str
            The text of the exception message, which will be surrounded by more details.

        method: str
            The HTTP method which resulted in the error, to display in the full message.

        path: str
            The path from which the error came, to display in the full message

        params: dict
            The query parameters passed as part of the request, to display in the full message.

        Returns
        -------
        NotFound
            The NotFound exception corresponding to the above arguments.

        """
        path_and_query = path + (f"?{urlencode(params)}" if params else "")
        return NotFound(
            path_and_query,
            SimpleNamespace(
                text=message,
                status_code=404,
                request=SimpleNamespace(method=method.upper()),
                reason="Not Found",
                json=lambda: {"code": 404, "message": message, "validation_errors": []}
            )
        )


class Unauthorized(NonRetryableHttpException):
    """Authentication or authorization failed (HTTP 401/403).

    Check that your API key is valid and that you have
    permission to access the requested resource.

    """

    pass


class BadRequest(NonRetryableHttpException):
    """The request was invalid (HTTP 400).

    Inspect ``api_error.validation_errors`` for details about
    which fields failed validation.

    """

    pass


class WorkflowConflictException(NonRetryableHttpException):
    """A conflict prevented the operation (HTTP 409).

    Another operation may be in progress on this resource.
    Wait and retry, or check for concurrent modifications.

    """

    pass


#: Alias for :class:`WorkflowConflictException`. A 409 can occur
#: in any context, not just workflows.
Conflict = WorkflowConflictException


class WorkflowNotReadyException(RetryableException):
    """The workflow is still validating (HTTP 425).

    This is a transient state. Use ``wait_while_validating()``
    to poll until the workflow is ready, or retry after a
    short delay.

    """

    pass


class PollingTimeoutError(NonRetryableException):
    """The client-side polling timeout was exceeded.

    The server-side job may still be running. Increase the
    ``timeout`` parameter to wait longer, or check the job
    status manually.

    """

    pass


class JobFailureError(NonRetryableException):
    """A server-side job completed with a failure status.

    Attributes
    ----------
    job_id : UUID
        The unique identifier of the failed job.
    failure_reasons : list[str]
        One reason string per failed task within the job.

    """

    def __init__(self, *, message: str, job_id: UUID, failure_reasons: List[str]):
        super().__init__(message)
        self.job_id = job_id
        self.failure_reasons = failure_reasons


class ModuleRegistrationFailedException(NonRetryableException):
    """A module (predictor, design space, etc.) failed to register.

    The original exception from the API is included in the
    message. Check that the module configuration is valid
    and that all referenced resources exist.

    """

    def __init__(self, moduleType: str, exc: Exception):
        err = 'The "{0}" failed to register. {1}: {2}'.format(
            moduleType, exc.__class__.__name__, str(exc))
        super().__init__(err)
