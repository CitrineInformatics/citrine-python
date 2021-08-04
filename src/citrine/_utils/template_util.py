import pandas as pd
from gemd.entity.object import (
    ProcessSpec,
    ProcessRun,
    MaterialSpec,
    MeasurementSpec,
    MeasurementRun,
)
from gemd.entity.attribute import PropertyAndConditions


def make_attribute_table(gems: list):
    """[ALPHA] the current status of make_attribute_table

    Given a list of GEMD Objects, this method returns a Pandas DataFrame
    where each row represents an attribute-containing
    Object and each column represent a unique Attribute Type + Name pair.
    The values within the cells are the various GEMD Value Types.

    """
    types_with_attributes = (
        ProcessSpec,
        ProcessRun,
        MaterialSpec,
        MeasurementSpec,
        MeasurementRun,
    )
    all_rows = []
    gems = [x for x in gems if isinstance(x, types_with_attributes)]
    for gem in gems:
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
    return pd.DataFrame(all_rows)
