"""Tools for working with design spaces."""
from typing import Type

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable


class Module(PolymorphicSerializable['Module']):
    """[ALPHA] A Citrine Module is a reusable computational tool used to construct a workflow.

    Abstract type that returns the proper type given a serialized dict.


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


class ModuleRef(Serializable['ModuleRef']):
    """[ALPHA] A reference to a Module by UID."""

    module_uid = properties.UUID('module_uid')

    def __init__(self, module_uid: str):
        self.module_uid = module_uid
