# flake8: noqa
"""A resource that represents a parameter attribute."""
import deprecation
from taurus.entity.attribute.parameter import Parameter as TaurusParameter


@deprecation.deprecated(deprecated_in="0.8.0", removed_in="0.9.0",
                        details="Use taurus.entity.attribute.parameter instead")
class Parameter(TaurusParameter):
    pass
