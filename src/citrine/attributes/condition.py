# flake8: noqa
"""A resource that represents a condition attribute."""
import deprecation
from gemd.entity.attribute.condition import Condition as GEMDCondition


@deprecation.deprecated(deprecated_in="0.8.0", removed_in="0.9.0",
                        details="Use gemd.entity.attribute.condition instead")
class Condition(GEMDCondition):
    pass
