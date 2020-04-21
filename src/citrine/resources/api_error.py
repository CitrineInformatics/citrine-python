from copy import copy
from typing import Optional, List

from gemd.entity.dict_serializable import DictSerializable


class ValidationError(DictSerializable):
    """A user-facing error message describing why their request was invalid."""

    def __init__(self, failure_message: Optional[str] = None, property: Optional[str] = None,
                 input: Optional[str] = None, failure_id: Optional[str] = None):
        self.failure_message = failure_message
        self.property = property
        self.input = input
        self.failure_id = failure_id


class ApiError(DictSerializable):
    """The engineering API root level error model."""

    def __init__(self, code: int, message: str, validation_errors: List[ValidationError] = None):
        self.code = code
        self.message = message
        self.validation_errors = validation_errors or []

    def has_failure(self, failure_id: str) -> bool:
        """Checks if this error contains a ValidationError with specified failure ID."""
        if not failure_id:
            # Discourage both anonymous errors ('') and confusing has_failure(None)
            # syntax which may imply there is no failure at all.
            raise ValueError("failure_id cannot be empty: '{}'".format(failure_id))
        return any(v.failure_id == failure_id for v in self.validation_errors)

    @classmethod
    def from_dict(cls, d):
        """Reconstitute the API error object from a dictionary."""
        d = copy(d)
        d.pop('debug_stacktrace', None)
        # TODO: deserialize to correct type automatically
        d['validation_errors'] = [ValidationError.from_dict(e)
                                  for e in d.get('validation_errors', [])]
        return cls(**d)
