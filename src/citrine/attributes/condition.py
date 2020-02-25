# flake8: noqa
"""A resource that represents a condition attribute."""
import deprecation
from taurus.entity.attribute.condition import Condition as TaurusCondition


@deprecation.deprecated(deprecated_in="0.8.0", removed_in="0.9.0",
                        details="Use taurus.entity.attribute.condition instead")
class Condition(TaurusCondition):
    pass
