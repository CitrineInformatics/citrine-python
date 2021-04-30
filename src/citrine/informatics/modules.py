"""Tools for working with design spaces."""
from typing import Type

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._rest.asynchronous_object import AsynchronousObject

__all__ = ['Module', 'ModuleRef']


class Module(PolymorphicSerializable['Module'], AsynchronousObject):
    """A Citrine Module is a reusable computational tool used to construct a workflow.

    Abstract type that returns the proper type given a serialized dict.

    All modules must inherit AIResourceMetadata, and hence have a ``status`` field.
    Possible statuses are CREATED, VALIDATING, INVALID, ERROR, and READY.

    """

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type['Module']:
        """Return the subtype."""
        from citrine.informatics.design_spaces import DesignSpace
        from citrine.informatics.processors import Processor
        from citrine.informatics.predictors import Predictor
        return {
            'DESIGN_SPACE': DesignSpace,
            'PROCESSOR': Processor,
            'PREDICTOR': Predictor
        }[data['module_type']].get_type(data)

    def in_progress(self) -> bool:
        return self.status == "VALIDATING" or self.status == "CREATED"

    def succeeded(self) -> bool:
        return self.status == "READY"

    def failed(self) -> bool:
        return self.status == "INVALID" or self.status == "ERROR"


class ModuleRef(Serializable['ModuleRef']):
    """A reference to a Module by UID."""

    module_uid = properties.UUID('module_uid')

    def __init__(self, module_uid: str):
        self.module_uid = module_uid
