from typing import Optional, Union
from uuid import UUID

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._rest.resource import Resource
from citrine._serialization import properties


__all__ = ["DefaultDesignSpaceMode", "DesignSpaceSettings"]


class DefaultDesignSpaceMode(BaseEnumeration):
    """The type of default design space to create.

    * ATTRIBUTE results in a product design space containing dimensions required by the predictor
    * HIERARCHICAL results in a hierarchical design space resembling the shape of training data
    """

    ATTRIBUTE = 'ATTRIBUTE'
    HIERARCHICAL = 'HIERARCHICAL'


class DesignSpaceSettings(Resource["DesignSpaceSettings"]):
    """The configuration used to produce a default design space."""

    predictor_id = properties.UUID("predictor_id")
    predictor_version = properties.Optional(
        properties.Union([properties.Integer(), properties.String()]),
        'predictor_version'
    )
    mode = properties.Optional(properties.Enumeration(DefaultDesignSpaceMode), "mode")
    exclude_intermediates = properties.Optional(properties.Boolean(), "exclude_intermediates")
    include_ingredient_fraction_constraints = properties.Optional(
        properties.Boolean(), "include_ingredient_fraction_constraints"
    )
    include_label_fraction_constraints = properties.Optional(
        properties.Boolean(), "include_label_fraction_constraints"
    )
    include_label_count_constraints = properties.Optional(
        properties.Boolean(), "include_label_count_constraints"
    )
    include_parameter_constraints = properties.Optional(
        properties.Boolean(), "include_parameter_constraints"
    )

    def __init__(self,
                 *,
                 predictor_id: Union[UUID, str],
                 predictor_version: Optional[Union[int, str]] = None,
                 mode: Optional[DefaultDesignSpaceMode] = None,
                 exclude_intermediates: Optional[bool] = None,
                 include_ingredient_fraction_constraints: Optional[bool] = None,
                 include_label_fraction_constraints: Optional[bool] = None,
                 include_label_count_constraints: Optional[bool] = None,
                 include_parameter_constraints: Optional[bool] = None):
        self.predictor_id = predictor_id
        self.predictor_version = predictor_version
        self.mode = mode
        self.exclude_intermediates = exclude_intermediates
        self.include_ingredient_fraction_constraints = include_ingredient_fraction_constraints
        self.include_label_fraction_constraints = include_label_fraction_constraints
        self.include_label_count_constraints = include_label_count_constraints
        self.include_parameter_constraints = include_parameter_constraints
