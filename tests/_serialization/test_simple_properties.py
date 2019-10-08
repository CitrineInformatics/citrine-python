import pytest
import arrow

from citrine._serialization.properties import Integer, String, Float, Datetime
from ._data import (
    VALID_SERIALIZATIONS,
    VALID_STRINGS,
    INVALID_DESERIALIZATION_TYPES,
    INVALID_INSTANCES,
    INVALID_SERIALIZED_INSTANCES,
)


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


@pytest.mark.parametrize('prop_type,serialized', INVALID_DESERIALIZATION_TYPES)
def test_invalid_deserialization_type(prop_type, serialized):
    prop = prop_type()
    with pytest.raises(ValueError):
        prop.deserialize(serialized)


@pytest.mark.parametrize('prop_type,path,expected', VALID_STRINGS)
def test_invalid_property_deserialization(prop_type, path, expected):
    assert expected == str(prop_type(path))


def test_serialize_to_dict_error():
    with pytest.raises(ValueError):
        Integer().serialize_to_dict({}, 1)


def test_valid_serialize_to_dict():
    assert {'my_foo': 100} == Integer('my_foo').serialize_to_dict({}, 100)


def test_serialize_dot_value_to_dict():
    assert {'my': {'foo': 100}} == Integer('my.foo').serialize_to_dict({}, 100)


def test_set_int_property_from_string():
    class Foo:
        bar = Integer('bar')

    f = Foo()
    f.bar = '12'

    assert 12 == f.bar


def test_string_property_deserialize_none():
    with pytest.raises(ValueError):
        String()._deserialize(None)


def test_int_cannot_deserialize_bool():
    with pytest.raises(TypeError):
        Integer()._deserialize(False)


def test_float_cannot_deserialize_bool():
    with pytest.raises(TypeError):
        Float()._deserialize(False)


def test_deserialize_string_datetime():
    assert arrow.get('2019-07-19T10:46:08+00:00').datetime == Datetime().deserialize('2019-07-19T10:46:08+00:00')


def test_datetime_cannot_deserialize_float():
    with pytest.raises(TypeError):
        Datetime()._deserialize(1.114)
