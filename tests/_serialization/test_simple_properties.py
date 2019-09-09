import pytest

from ._data import VALID_SERIALIZATIONS, INVALID_INSTANCES, INVALID_SERIALIZED_INSTANCES


@pytest.mark.parametrize('prop_type,value,serialized', VALID_SERIALIZATIONS)
def test_simple_property_serde(prop_type, value, serialized):
    prop = prop_type()
    assert prop.deserialize(serialized) == value
    assert prop.serialize(value) == serialized


@pytest.mark.parametrize('prop_type,value', INVALID_INSTANCES)
def test_invalid_property_serialization(prop_type, value):
    prop = prop_type()
    with pytest.raises(Exception):
        prop.serialize(value)


@pytest.mark.parametrize('prop_type,serialized', INVALID_SERIALIZED_INSTANCES)
def test_invalid_property_deserialization(prop_type, serialized):
    prop = prop_type()
    with pytest.raises(Exception):
        prop.deserialize(serialized)


