"""Definitions for GemdQuery objects, and their sub-objects."""
from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._serialization.serializable import Serializable
from citrine._serialization import properties
from citrine.gemd_queries.criteria import Criteria


class GemdObjectType(BaseEnumeration):
    """The style of text search to run."""

    # An old defect has some old GemdQuery values stored with invalid enums
    # The synonyms will allow invalid old values to be read, but not emitted
    MEASUREMENT_TEMPLATE_TYPE = "measurement_template", "MEASUREMENT_TEMPLATE_TYPE"
    MATERIAL_TEMPLATE_TYPE = "material_template", "MATERIAL_TEMPLATE_TYPE"
    PROCESS_TEMPLATE_TYPE = "process_template", "PROCESS_TEMPLATE_TYPE"
    PROPERTY_TEMPLATE_TYPE = "property_template", "PROPERTY_TEMPLATE_TYPE"
    CONDITION_TEMPLATE_TYPE = "condition_template", "CONDITION_TEMPLATE_TYPE"
    PARAMETER_TEMPLATE_TYPE = "parameter_template", "PARAMETER_TEMPLATE_TYPE"
    PROCESS_RUN_TYPE = "process_run", "PROCESS_RUN_TYPE"
    PROCESS_SPEC_TYPE = "process_spec", "PROCESS_SPEC_TYPE"
    MATERIAL_RUN_TYPE = "material_run", "MATERIAL_RUN_TYPE"
    MATERIAL_SPEC_TYPE = "material_spec", "MATERIAL_SPEC_TYPE"
    INGREDIENT_RUN_TYPE = "ingredient_run", "INGREDIENT_RUN_TYPE"
    INGREDIENT_SPEC_TYPE = "ingredient_spec", "INGREDIENT_SPEC_TYPE"
    MEASUREMENT_RUN_TYPE = "measurement_run", "MEASUREMENT_RUN_TYPE"
    MEASUREMENT_SPEC_TYPE = "measurement_spec", "MEASUREMENT_SPEC_TYPE"


class GemdQuery(Serializable['GemdQuery']):
    """
    This describes what data objects to fetch (or graph of data objects).

    Parameters
    ----------
    criteria: Criteria
        List of conditions all responses must satisfy (i.e., joined with an AND).
    datasets: UUID
        Set of datasets to look in for matching objects.
    object_types: GemdObjectType
        Classes of objects to consider when searching.
    schema_version: Int
        What version of the query schema this package represents.

    """

    criteria = properties.List(properties.Object(Criteria), "criteria", default=[])
    datasets = properties.Set(properties.UUID, "datasets", default=set())
    object_types = properties.Set(
        properties.Enumeration(GemdObjectType),
        'object_types',
        default={x for x in GemdObjectType}
    )
    schema_version = properties.Integer('schema_version', default=1)

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        """Run data modification before building."""
        version = data.get('schema_version')
        if data.get('schema_version') != 1:
            raise ValueError(
                f"This version of the library only supports schema_version 1, not '{version}'"
            )
        return data
