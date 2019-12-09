import pytest
import arrow
import uuid

from citrine.resources.dataset import Dataset
from citrine._serialization.properties import (
    Integer,
    String,
    Float,
    UUID,
    Datetime,
    LinkByUID,
    LinkOrElse,
    MixedList,
    Object,
    Optional,
)
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


@pytest.mark.parametrize('prop_type,serialized', INVALID_DESERIALIZATION_TYPES)
def test_invalid_deserialization_type_with_base_class(prop_type, serialized):
    class BaseTest:
        pass

    prop = prop_type()
    prop.serialization_path = 'ser_path'
    with pytest.raises(ValueError) as excinfo:
        prop.deserialize(serialized, base_class=BaseTest().__class__)

    # Check that the exception includes the calling class name and argument
    if not isinstance(prop, UUID):
        assert 'BaseTest:ser_path' in str(excinfo.value)


@pytest.mark.parametrize('prop_type,serialized', INVALID_DESERIALIZATION_TYPES)
def test_invalid_deserialization_type_with_dataset(prop_type, serialized):
    # Supplying a Daatset instance as the base_class should include it's
    # name in the exception value string (UUIDs are a special case)
    dset = Dataset(name="dset", summary="test dataset", description="description")

    prop = prop_type()
    prop.serialization_path = 'ser_path'
    with pytest.raises(ValueError) as excinfo:
        prop.deserialize(serialized, base_class=dset.__class__)

    if not isinstance(prop, UUID):
        assert 'Dataset:ser_path' in str(excinfo.value)


@pytest.mark.parametrize('prop_type,path,expected', VALID_STRINGS)
def test_valid_property_deserialization(prop_type, path, expected):
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


def test_mixed_list_requires_property_list():
    with pytest.raises(ValueError):
        MixedList(Integer)


def test_deserialize_mixed_list():
    ml = MixedList([Integer, String])
    assert [1, '2'] == ml.deserialize([1, '2'])
    assert [1, None] == ml.deserialize([1])


def test_mixed_list_cannot_deserialize_larger_lists():
    ml = MixedList([Integer])
    with pytest.raises(ValueError):
        ml.deserialize([1, '2'])
    with pytest.raises(ValueError):
        ml.deserialize([1, 2])


def test_mixed_list_cannot_serialize_larger_lists():
    ml = MixedList([Integer])
    with pytest.raises(ValueError):
        ml.serialize([1, '2'])
    with pytest.raises(ValueError):
        ml.serialize([1, 2])


def test_mixed_list_with_defaults():
    ml = MixedList([Integer, Integer, Integer(default=100)])
    assert [1, 2, 100] == ml.serialize([1, 2])


def test_invalid_object_deserialize():
    class Foo:
        pass

    obj = Object(Foo)
    with pytest.raises(AttributeError):
        obj.deserialize({'key': 'value'})


def test_linkorelse_deserialize_requires_serializable():
    loe = LinkOrElse()
    with pytest.raises(Exception):
        loe.deserialize({})


def test_linkorelse_deserialize_requires_scope_and_id():
    loe = LinkOrElse()
    with pytest.raises(ValueError):
        loe.deserialize({'type': LinkByUID.typ})


def test_linkorelse_deserialize():
    loe = LinkOrElse()
    lbu = loe.deserialize({'type': LinkByUID.typ, 'scope': 'foo', 'id': uuid.uuid4()})
    assert isinstance(lbu, LinkByUID)


def test_optional_repr():
    opt = Optional(String)
    assert '<Optional[<String None>] None>' == str(opt)
