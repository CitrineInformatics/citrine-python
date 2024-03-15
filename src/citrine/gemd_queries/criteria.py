"""Definitions for GemdQuery objects, and their sub-objects."""
from typing import List, Type

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties
from citrine.gemd_queries.filter import PropertyFilterType

__all__ = ['MaterialClassification', 'TextSearchType',
           'AndOperator', 'OrOperator',
           'PropertiesCriteria', 'NameCriteria',
           'MaterialRunClassificationCriteria', 'MaterialTemplatesCriteria'
           ]


class MaterialClassification(BaseEnumeration):
    """A classification based on where in a Material History you find a Material."""

    ATOMIC_INGREDIENT = "atomic_ingredient"
    INTERMEDIATE_INGREDIENT = "intermediate_ingredient"
    TERMINAL_MATERIAL = "terminal_material"


class TextSearchType(BaseEnumeration):
    """The style of text search to run."""

    EXACT = "exact"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    SUBSTRING = "substring"


class Criteria(PolymorphicSerializable):
    """Abstract concept of a criteria to apply when searching for materials."""

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        classes: List[Type[Criteria]] = [
            AndOperator, OrOperator,
            PropertiesCriteria, NameCriteria, MaterialRunClassificationCriteria,
            MaterialTemplatesCriteria
        ]
        return {klass.typ: klass for klass in classes}[data['type']]


class AndOperator(Serializable['AndOperator'], Criteria):
    """
    Combine multiple criteria, requiring EACH to be true for a match.

    Parameters
    ----------
    criteria: Criteria
        List of conditions all responses must satisfy (i.e., joined with an AND).

    """

    criteria = properties.List(properties.Object(Criteria), "criteria")
    typ = properties.String('type', default="and_operator", deserializable=False)


class OrOperator(Serializable['OrOperator'], Criteria):
    """
    Combine multiple criteria, requiring ANY to be true for a match.

    Parameters
    ----------
    criteria: Criteria
        List of conditions, at least one of which must match (i.e., joined with an OR).

    """

    criteria = properties.List(properties.Object(Criteria), "criteria")
    typ = properties.String('type', default="or_operator", deserializable=False)


class PropertiesCriteria(Serializable['PropertiesCriteria'], Criteria):
    """
    Look for materials with a particular Property and optionally Value types & ranges.

    Parameters
    ----------
    property_templates_filter: Set[UUID]
        The citrine IDs of the property templates matches must reference.
    value_type_filter: Optional[PropertyFilterType]
        The value range matches must conform to.

    """

    property_templates_filter = properties.Set(properties.UUID, "property_templates_filter")
    value_type_filter = properties.Optional(
        properties.Object(PropertyFilterType), "value_type_filter"
    )
    typ = properties.String('type', default="properties_criteria", deserializable=False)


class NameCriteria(Serializable['NameCriteria'], Criteria):
    """
    Look for materials with particular names.

    Parameters
    ----------
    name: str
        The name the returned objects must have.
    search_type: TextSearchType
        What kind of string match to use (exact, substring, ...).

    """

    name = properties.String('name')
    search_type = properties.Enumeration(TextSearchType, 'search_type')
    typ = properties.String('type', default="name_criteria", deserializable=False)


class MaterialRunClassificationCriteria(
    Serializable['MaterialRunClassificationCriteria'],
    Criteria
):
    """
    Look for materials with particular classification, defined by MaterialClassification.

    Parameters
    ----------
    classifications: Set[MaterialClassification]
        The classification, based on where in a material history an object appears.

    """

    classifications = properties.Set(
        properties.Enumeration(MaterialClassification), 'classifications'
    )
    typ = properties.String(
        'type',
        default="material_run_classification_criteria",
        deserializable=False
    )


class MaterialTemplatesCriteria(Serializable['MaterialTemplatesCriteria'], Criteria):
    """
    Look for materials with particular Material Templates and tags.

    This has a similar behavior to the old [[MaterialRunByTemplate]] Row definition

    Parameters
    ----------
    material_templates_identifiers: Set[UUID]
        Which material templates to filter by.
    tag_filters: Set[str]
        Which tags to filter by.

    """

    material_templates_identifiers = properties.Set(
        properties.UUID,
        "material_templates_identifiers"
    )
    tag_filters = properties.Set(properties.String, 'tag_filters')
    typ = properties.String('type', default="material_template_criteria", deserializable=False)
