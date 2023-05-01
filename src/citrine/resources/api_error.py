from citrine._serialization import properties
from citrine._serialization.serializable import Serializable


class ValidationError(Serializable["ValidationError"]):
    """A user-facing error message describing why their request was invalid."""

    failure_message = properties.Optional(properties.String(), "failure_message")
    property = properties.Optional(properties.String(), "property")
    input = properties.Optional(properties.String(), "input")
    failure_id = properties.Optional(properties.String(), "failure_id")


class ApiError(Serializable["ApiError"]):
    """The engineering API root level error model."""

    code = properties.Optional(properties.Integer(), "code")
    message = properties.Optional(properties.String(), "message")
    validation_errors = properties.List(properties.Object(ValidationError), "validation_errors")

    def has_failure(self, failure_id: str) -> bool:
        """Checks if this error contains a ValidationError with specified failure ID."""
        if not failure_id:
            # Discourage both anonymous errors ('') and confusing has_failure(None)
            # syntax which may imply there is no failure at all.
            raise ValueError(f"failure_id cannot be empty: '{failure_id}'")
        return any(v.failure_id == failure_id for v in self.validation_errors)
