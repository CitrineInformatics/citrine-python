from gemd.util.impl import recursive_flatmap
from gemd.entity.object import (
    ProcessSpec,
    ProcessRun,
    MaterialSpec,
    MeasurementSpec,
    MeasurementRun,
)
from citrine.resources.data_concepts import DataConcepts
from gemd.entity.value.base_value import BaseValue
from typing import Mapping, List
from gemd.entity.attribute import PropertyAndConditions


def make_attribute_table(gems: List[DataConcepts]) -> List[Mapping[str, BaseValue]]:
    """[ALPHA] the current status of make_attribute_table.

    Given a list of GEMD Objects, this method returns a list of dictionaries
    where in each dictionary there are keys of "object", "object_type" and keys for each
    unique Attribute Type + Name pair found within those Objects.
    Each value contains the associated Object, Object Type, or BaseValue.
    This dictionary can easily be converted into a Pandas DataFrame where there is a
    row for each Object, and the values within the cells are that Object's type or
    the various GEMD Value Types.

    This function will help users identify attribute usage across their Objects,
    and get a sense of the consistency of the data found in their GEMD objects.
    With the returned dictionary, one can easily do further analysis on both
    attribute values and value type consistency to assist in data cleaning and
    Attribute Template creation.

    Parameters
    ----------
    gems : List[DataConcepts]
        List of GEMD objects whose attributes you would like to compare.

    Returns
    -------
    List[Mapping[str, BaseValue]]
        A list of dictionaries where each dictionary represents an object and its attributes.

    """
    flattened_gems = recursive_flatmap(
        obj=gems, func=lambda x: [x], unidirectional=False
    )
    types_with_attributes = (
        ProcessSpec,
        ProcessRun,
        MaterialSpec,
        MeasurementSpec,
        MeasurementRun,
    )
    all_rows = []
    attributed_gems = [
        x for x in flattened_gems if isinstance(x, types_with_attributes)
    ]
    for gem in attributed_gems:
        row_dict = {"object": gem, "object_type": type(gem).__name__}
        if hasattr(gem, "conditions"):
            for cond in gem.conditions:
                row_dict[f"CONDITION: {cond.name}"] = cond.value
        if hasattr(gem, "parameters"):
            for param in gem.parameters:
                row_dict[f"PARAMETER: {param.name}"] = param.value
        if hasattr(gem, "properties"):
            for prop in gem.properties:
                if isinstance(prop, PropertyAndConditions):
                    row_dict[f"PROPERTY: {prop.property.name}"] = prop.property.value
                    for cond in prop.conditions:
                        row_dict[f"CONDITION: {cond.name}"] = cond.value
                else:
                    row_dict[f"PROPERTY: {prop.name}"] = prop.value
        all_rows.append(row_dict)
    return all_rows
