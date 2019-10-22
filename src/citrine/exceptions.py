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
        super().__init__(path)
        self.url = path


class Unauthorized(NonRetryableException):
    """The user is unauthorized to make this api call. (http status 401)."""

    def __init__(self, path: str):
        super().__init__(path)
        self.url = path


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
