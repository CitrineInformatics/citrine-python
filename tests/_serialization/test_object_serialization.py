import pytest
from typing import Any

from citrine._serialization.serializable import Serializable
from citrine._serialization.properties import String, Object, Optional
from gemd.entity.value.base_value import BaseValue
from gemd.entity.value.nominal_real import NominalReal


class UnserializableClass:
    """A dummy class that has no clear serialization or deserialization method."""
    def __init__(self, foo):
        self.foo = foo


class SampleClass(Serializable):
    """A class to stress the deser scheme's ability to handle objects."""
    prop_string = String('prop_string.string', default='default')
    prop_value = Object(BaseValue, 'prop_value')
    prop_object = Optional(Object(UnserializableClass), 'prop_object')

    def __init__(self, prop_string: str, prop_value: BaseValue, prop_object: Any = None):
        self.prop_string = prop_string
        self.prop_value = prop_value
        self.prop_object = prop_object


def test_gemd_object_serde():
    """Test that an unspecified gemd object can be serialized and deserialized."""
    good_obj = SampleClass("Can be serialized", NominalReal(17, ''))
    copy = SampleClass.build(good_obj.dump())
    assert copy.prop_value == good_obj.prop_value
    assert copy.prop_string == good_obj.prop_string


def test_default_nested_serde():
    """Test that defaults work in nested dictionaries."""
    good_obj = SampleClass("Can be serialized", NominalReal(17, ''))
    data = good_obj.dump()

    # If 'prop_string.string' is a non-string, that's an error
    data['prop_string']['string'] = 0
    with pytest.raises(ValueError):
        SampleClass.build(data)

    # If data['prop_string'] is an empty dictionary, then the default is used
    data['prop_string'] = dict()
    assert SampleClass.build(data).prop_string == 'default'

    # If `data` does not even have a 'prop_string' key, then the default is used
    del data['prop_string']
    assert SampleClass.build(data).prop_string == 'default'


def test_bad_object_serde():
    """Test that a 'mystery' object cannot be serialized."""
    bad_obj = SampleClass("Cannot be serialized", NominalReal(34, ''), UnserializableClass(1))
    with pytest.raises(AttributeError):
        bad_obj.dump()


def test_object_str_representation():
    assert "<Object[NominalReal] 'foo'>" == str(Object(NominalReal, 'foo'))


def test_override_configurations():
    """Check that weird override cases get caught."""
    class OverrideTestClass(Serializable['OverrideTestClass']):
        overridden_value = String("overridden_value", override=True)
        overridden_option = Optional(String(), "overridden_option", override=True)

    with pytest.raises(AttributeError, match="overridden_value"):
        OverrideTestClass.build(data={"overridden_value": "string"})

    obj = OverrideTestClass()
    with pytest.raises(AttributeError, match="overridden_value"):
        obj.overridden_value = "1"
    with pytest.raises(AttributeError, match="overridden_option"):
        obj.overridden_option = "1"
    with pytest.raises(AttributeError, match="overridden_value"):
        _ = obj.overridden_value


def test_override_read_only():
    """Check that weird override cases get caught."""

    class BaseTestClass:
        def __init__(self, required, initable="Me"):
            self._no_key = None
            self._required = required
            self._initable = initable

        @property
        def initable(self):
            return self._initable

        @property
        def required(self):
            return self._required

    class OverrideTestClass(Serializable['OverrideTestClass'], BaseTestClass):
        no_key = Optional(String(), "no_key", override=True)
        initable = Optional(String(), "initable", override=True, use_init=True)
        required = String("required", override=True, use_init=True)

    with pytest.raises(AttributeError, match="no_key"):
        OverrideTestClass.build(data={"no_key": "string", "required": "value"})

    obj = OverrideTestClass(required="I was required")
    with pytest.raises(AttributeError, match="no_key"):
        obj.no_key = "1"
    with pytest.raises(AttributeError, match="no_key"):
        _ = obj.no_key
    with pytest.raises(AttributeError, match="can't set"):
        obj.initable = "1"
    with pytest.raises(AttributeError, match="can't set"):
        obj.required = "1"


def test_init_props():
    """Test exceptions around use_init."""

    class TestClass:
        def __init__(self, required, *, optional=None):
            self._required = None
            self.required = required

        @property
        def required(self):
            return self._required

        @required.setter
        def required(self, value):
            if value == "magic_value":
                raise TypeError("magic_value")
            self._required = value

    class BadClass(Serializable['BadClass'], TestClass):
        required = String("required", override=True)
        optional = Optional(String(), "optional", use_init=True)

    class GoodClass(Serializable['BadClass'], TestClass):
        required = Optional(String(), "required", override=True, use_init=True)
        optional = Optional(String(), "optional", use_init=True)

    with pytest.raises(AttributeError, match="use_init"):
        BadClass.build({"required": "value", "optional": "value"})

    with pytest.raises(TypeError):
        GoodClass.build({"required": "magic_value", "optional": "value"})
