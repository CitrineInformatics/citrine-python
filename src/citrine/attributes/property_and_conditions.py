# flake8: noqa
"""A resource that represents a property attribute."""
import deprecation
from gemd.entity.attribute.property_and_conditions import PropertyAndConditions as \
    GEMDPropertyAndConditions


@deprecation.deprecated(deprecated_in="0.8.0", removed_in="0.9.0",
                        details="Use gemd.entity.attribute.property_and_conditions instead")
class PropertyAndConditions(GEMDPropertyAndConditions):
    pass
