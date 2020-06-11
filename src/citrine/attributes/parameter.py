# flake8: noqa
"""A resource that represents a parameter attribute."""
import deprecation
from gemd.entity.attribute.parameter import Parameter as GEMDParameter


@deprecation.deprecated(deprecated_in="0.8.0", removed_in="0.9.0",
                        details="Use gemd.entity.attribute.parameter instead")
class Parameter(GEMDParameter):
    pass
