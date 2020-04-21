import pytest

from citrine._rest.resource import Resource
from gemd.entity.object.process_spec import ProcessSpec

from citrine.resources.object_specs import ObjectSpec


def test_invalid_client_field():
    """Ensure we get a NotImplementedError as a result of defining a class with unsupported client fields."""
    class BadProcessSpec(ObjectSpec, Resource['ProcessSpec'], ProcessSpec):
        client_specific_fields = {
            'foo': int,
        }
    with pytest.raises(NotImplementedError):
        BadProcessSpec.from_dict({'name': 'Mr. Foo', 'typ': 'process_spec', 'foo': 1})
