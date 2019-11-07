"""Tools for working with design spaces."""
from typing import Any, List, Mapping, Type
from uuid import UUID

from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable


class Module(PolymorphicSerializable['Module']):
    """A Citrine Module - an abstract type that returns the proper
    subtype based on the 'type' value of the passed in dict.
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