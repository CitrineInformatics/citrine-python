import uuid

import arrow
import pytest
from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._serialization.properties import (
    Datetime,
    Enumeration,
    Float,
    Integer,
    LinkByUID,
    LinkOrElse,
    Set,
    SpecifiedMixedList,
    Object,
    Optional,
    String,
    Union,
    UUID,
)
from citrine.informatics.predictor_evaluation_metrics import PredictorEvaluationMetric, RMSE, CoverageProbability
from citrine.resources.dataset import Dataset
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
        SpecifiedMixedList(Integer)


def test_deserialize_mixed_list():
    ml = SpecifiedMixedList([Integer, String])
    assert [1, '2'] == ml.deserialize([1, '2'])
    assert [1, None] == ml.deserialize([1])


def test_mixed_list_cannot_deserialize_larger_lists():
    ml = SpecifiedMixedList([Integer])
    with pytest.raises(ValueError):
        ml.deserialize([1, '2'])
    with pytest.raises(ValueError):
        ml.deserialize([1, 2])


def test_mixed_list_cannot_serialize_larger_lists():
    ml = SpecifiedMixedList([Integer])
    with pytest.raises(ValueError):
        ml.serialize([1, '2'])
    with pytest.raises(ValueError):
        ml.serialize([1, 2])


def test_mixed_list_with_defaults():
    ml = SpecifiedMixedList([Integer, Integer, Integer(default=100)])
    assert [1, 2, 100] == ml.serialize([1, 2])


def test_union():
    # Attempt to de/serialize first with Integer, then LinkOrElse, then String
    union_type = Union([Integer, LinkOrElse, String])
    assert 3 == union_type.deserialize(3)
    assert 3 == union_type.serialize(3)
    # Since "3" can be deserialized with Integer, this deserializes as an int
    assert 3 == union_type.deserialize("3")
    assert "3" == union_type.serialize("3")
    with pytest.raises(ValueError):
        union_type.deserialize(1.7)


def test_untion_requires_property_iterable():
    with pytest.raises(ValueError):
        Union(Integer)


class EnumerationExample(BaseEnumeration):
    FOO = "foo"
    BAR = "bar"


def test_union_runtime_errors():
    """
    De/serialization of Union ignores value errors.
    They indicate that a specific property is not the one that should be used for de/ser.

    If a different type of value error occurs then it can result in a difficult-to-diagnose
    error state and a runtime error is thrown.
    This test illustrates how that can happen for both serialization and deserialization.

    """
    # The underlying type is correct (BaseEnumeration) but FOO is not part of that enumeration
    with pytest.raises(RuntimeError):
        Union([Enumeration(BaseEnumeration)]).serialize(EnumerationExample.FOO)
    # The serialized type is correct (dict) but it is missing fields
    incomplete_dataset_dict = {'name': 'name'}
    with pytest.raises(ValueError):
        Union([Object(Dataset)]).deserialize(incomplete_dataset_dict)


def test_enumeration_ser():
    assert Enumeration(EnumerationExample).serialize(EnumerationExample.FOO) == "foo"


def test_enumeration_deser():
    assert Enumeration(EnumerationExample).deserialize("foo") == EnumerationExample.FOO
    with pytest.raises(ValueError):
        Enumeration(EnumerationExample).deserialize("baz")


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


def test_set_serialize_sortable():
    data = {3, 2, 1}
    serialized = Set(Integer).serialize(data)
    # if items in the set are sortable, the list should be returned in sorted order
    assert serialized == [1, 2, 3]


def test_set_serialize_unsortable():
    """
    Serializing a set of predictor evaluation metrics results
    in a list of dictionaries, which cannot be sorted.
    Attempting to serialize the data should work, but the order
    cannot be guaranteed, hence why we assert each metric is in
    the serialized value individually.

    """
    data = {RMSE(), CoverageProbability()}
    serialized = Set(Object(PredictorEvaluationMetric)).serialize(data)
    for metric in data:
        assert metric.dump() in serialized
