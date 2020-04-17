# flake8: noqa
"""A resource that represents a property attribute."""
import deprecation
from gemd.entity.attribute.property import Property as GEMDProperty


@deprecation.deprecated(deprecated_in="0.8.0", removed_in="0.9.0",
                        details="Use gemd.entity.attribute.property instead")
class Property(GEMDProperty):
    pass

