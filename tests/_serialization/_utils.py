from typing import Type, Any

from citrine._serialization import properties


def make_class_with_property(prop_type: Type[properties.Property], field_name: str):
    class SampleObject:
        def __init__(self, field_value: Any):
            setattr(self, field_name, field_value)

        def __eq__(self, other):
            return getattr(self, field_name) == getattr(other, field_name)
    setattr(SampleObject, field_name, prop_type(field_name))
    return SampleObject
