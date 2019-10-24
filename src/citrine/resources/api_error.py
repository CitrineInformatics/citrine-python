from typing import Optional, List

from taurus.entity.dict_serializable import DictSerializable


class ValidationError(DictSerializable):

    def __init__(self, failure_message: Optional[str], property: Optional[str], input: Optional[str]):
        self.failure_message = failure_message
        self.property = property
        self.input = input


class ApiError(DictSerializable):

    def __init__(self, code: int, message: str, validation_errors: List[ValidationError]):
        self.code = code
        self.message = message
        self.validation_errors = validation_errors
