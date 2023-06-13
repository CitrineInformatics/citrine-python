"""Property objects for typed setting and ser/de."""
from abc import abstractmethod
import typing
from datetime import datetime
from inspect import signature
from itertools import chain
import uuid
import arrow
from functools import lru_cache
import re

from gemd.enumeration.base_enumeration import BaseEnumeration
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.dict_serializable import DictSerializable
from gemd.util.impl import cached_isinstance as isinstance

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable

SerializedType = typing.TypeVar('SerializedType')
DeserializedType = typing.TypeVar('DeserializedType')
SerializedInteger = typing.TypeVar('SerializedInteger', int, str)
SerializedFloat = typing.TypeVar('SerializedFloat', float, str)


class Property(typing.Generic[DeserializedType, SerializedType]):
    """
    Basic operating unit of a serialization layer.

    By defining a Property as a class variable, access methods are defined and
    a type-aware deserialization method is implemented for translating between
    a dictionary-based representation and a Python object based representation.

    Parameters
    ----------
    serialization_path: str
        The location in the serialized structure where the value of interest can be
        found.  The value can be nested in the structure, where separate keys are
        joined by `.`.  Required in a top level property, but not necessary if
        a property is wrapped by a container.
    serializable: bool
        Include the field when serializing an object to a dictionary; default: True
    deserializable: bool
        Look for the field when deserializing a dictionary into an object; default: True
    default:  DeserializedType
        If no value is found in an incoming dictionary, which value to use; default: None
    override: bool
        Use a parent class' accessor methods; default: False
    use_init: bool
        When deserializing, use the __init__ method instead of the setter

    """

    def __init__(self,
                 serialization_path: typing.Optional[str] = None,
                 *,
                 serializable: bool = True,
                 deserializable: bool = True,
                 default: typing.Optional[DeserializedType] = None,
                 override: bool = False,
                 use_init: bool = False
                 ):
        self.serialization_path = serialization_path
        if override:
            self._key: None = None
        else:
            self._key: str = '__' + str(uuid.uuid4())  # Make this object key human-readable
        self.serializable: bool = serializable
        self.deserializable: bool = deserializable
        self.default: typing.Optional[DeserializedType] = default
        # Distinguish between no default being provided and the default being None
        self.optional: bool = False
        self.use_init: bool = use_init

    @property
    @abstractmethod
    def underlying_types(self) -> typing.Union[DeserializedType, typing.Tuple[DeserializedType]]:
        """Return the python types handled by this property."""

    @property
    @abstractmethod
    def serialized_types(self) -> typing.Union[SerializedType, typing.Tuple[SerializedType]]:
        """Return the types used to serialize this property."""

    def _error_source(self, base_class: type) -> str:
        """Construct a string of the base class name and the parameter that failed."""
        if base_class is not None:
            return ' for {}:{}'.format(base_class.__name__, self.serialization_path)
        elif self.serialization_path:
            return ' for {}'.format(self.serialization_path)
        else:
            return ''

    def serialize(self, value: DeserializedType,
                  base_class: typing.Optional[type] = None) -> SerializedType:
        if not isinstance(value, self.underlying_types):
            base_name = self._error_source(base_class)
            raise ValueError(
                f'{type(value)} {value} is not one of valid types: '
                f'{self.underlying_types}{base_name}'
            )
        return self._serialize(value)

    def deserialize(self, value: SerializedType,
                    base_class: typing.Optional[type] = None) -> DeserializedType:
        if not isinstance(value, self.serialized_types):
            if isinstance(value, self.underlying_types):
                return value  # Don't worry if it was already deserialized
            base_name = self._error_source(base_class)
            raise ValueError(
                f'{type(value)} {value} is not one of valid types: '
                f'{self.serialized_types}{base_name}'
            )
        return self._deserialize(value)

    @abstractmethod
    def _serialize(self, value: DeserializedType) -> SerializedType:
        """Perform serialization."""

    @abstractmethod
    def _deserialize(self, value: SerializedType) -> DeserializedType:
        """Perform deserialization."""

    def deserialize_from_dict(self, data: dict) -> DeserializedType:
        value = data
        # `serialization_path` is expected to be a sequence of nested dictionary keys
        fields = self.serialization_path.split('.')
        for field in fields:
            next_value = value.get(field)
            if next_value is None:
                if self.default is None and not self.optional:
                    msg = "Unable to deserialize {} into {}, missing a required field: {}".format(
                        data, self.underlying_types, field)
                    raise ValueError(msg)
                # This occurs if a `field` is unexpectedly not present in the data dictionary
                # or if its value is null.
                # Use the default value and stop traversing, even if we have not yet reached
                # the last field in the serialization path.
                value = self.serialize(self.default)
                break
            else:
                value = next_value
        return self.deserialize(value, base_class=None)  # always a dict

    def serialize_to_dict(self, data: dict, value: DeserializedType) -> dict:
        if self.serialization_path is None:
            raise ValueError('No serialization path set!')

        _data = data
        fields = self.serialization_path.split('.')
        for field in fields[:-1]:
            _data = _data.setdefault(field, {})
        _data[fields[-1]] = self.serialize(value, base_class=None)  # Always a dict
        return data

    def __get__(self, obj, objtype=None) -> DeserializedType:
        """Property getter, deferring to the getter of the parent class, if applicable."""
        if self._key is None:
            property_name, base_class = _get_key_and_base_class(self, type(obj))
            if base_class is not None:
                return getattr(base_class, property_name).fget(obj)
            else:
                raise AttributeError(
                    f"No parent class could be resolved for '{property_name}' "
                    f"in {obj.__class__}.  'override' should probably be false."
                )
        else:
            return getattr(obj, self._key, self.default)

    def __set__(self, obj, value: typing.Union[SerializedType, DeserializedType]):
        """Property setter, deferring to the setter of the parent class, if applicable."""
        property_name, base_class = _get_key_and_base_class(self, type(obj))
        if issubclass(type(value), self.underlying_types):
            value_to_set = value
        else:
            # if value is not an underlying type, set its deserialized version.
            value_to_set = self.deserialize(value, base_class=base_class)

        if self._key is None:
            if base_class is not None:
                prop = getattr(base_class, property_name)
                if prop.fset is not None:  # It's a property with a setter
                    prop.fset(obj, value_to_set)
                else:  # It's a read-only property
                    raise AttributeError(f"can't set attribute '{property_name}'")
            else:
                raise AttributeError(
                    f"No parent class could be resolved for '{property_name}' in "
                    f"{obj.__class__}.  'override' should probably be false."
                )
        else:
            setattr(obj, self._key, value_to_set)

    def __str__(self):
        return '<Property {!r}>'.format(self.serialization_path)


class PropertyCollection(Property[DeserializedType, SerializedType]):

    def __set__(self, obj, value: typing.Union[SerializedType, DeserializedType]):
        """
        Property setter for container property types.

        This setter defers to the subclass to implement the `_set_elements` logic
        """
        property_name, base_class = _get_key_and_base_class(self, type(obj))
        if issubclass(type(value), self.underlying_types):
            value_to_set = self._set_elements(value)
        elif issubclass(type(value), self.serialized_types):
            # if value is not an underlying type, set its deserialized version.
            value_to_set = self.deserialize(value, base_class=base_class)
        else:
            raise TypeError(
                f"{value} is a {type(value)}, but {property_name} expects one of: "
                f"{self.underlying_types}"
            )

        if self._key is None:
            if base_class is not None:
                prop = getattr(base_class, property_name)
                if prop.fset is not None:  # It's a property with a setter
                    prop.fset(obj, value_to_set)
                else:  # It's a read-only property
                    raise AttributeError(f"can't set attribute '{property_name}'")
            else:
                raise AttributeError(
                    f"No parent class could be resolved for '{property_name}' "
                    f"in {obj.__class__}.  'override' should probably be false."
                )
        else:
            setattr(obj, self._key, value_to_set)

    @abstractmethod
    def _set_elements(self, value: typing.Union[SerializedType, DeserializedType]):
        """
        Perform any needed underlying element specific deserialization.

        Return the appropriate value to set
        """


@lru_cache(maxsize=1024)
def _get_key_and_base_class(prop: Property, klass: typing.Any) -> \
        typing.Tuple[typing.Optional[str], typing.Optional[str]]:
    """
    Return the base class and class attribute name for the object and property.

    Uses method resolution order to determine which base class would handle it.
    """
    mro = klass.__mro__  # Tuple of all base classes of obj
    key = next((k for c in mro for k, v in c.__dict__.items() if v == prop), None)
    if key is None:
        return None, None

    base_class = next((b for b in klass.__bases__ if hasattr(b, key)), None)
    return key, base_class


class Integer(Property[int, SerializedInteger]):

    @property
    def underlying_types(self):
        return int

    @property
    def serialized_types(self):
        return int, str

    def _deserialize(self, value: SerializedInteger) -> int:
        if isinstance(value, bool):
            raise TypeError('value must be a Number, not a boolean.')
        else:
            return int(value)

    def _serialize(self, value: int) -> SerializedInteger:
        if isinstance(value, bool):
            raise TypeError('Boolean cannot be serialized to integer.')
        else:
            return value

    def __str__(self):
        return '<Integer {!r}>'.format(self.serialization_path)


class Float(Property[float, SerializedFloat]):

    @property
    def underlying_types(self):
        return float

    @property
    def serialized_types(self):
        return float, int, str

    @classmethod
    def _deserialize(cls, value: SerializedFloat) -> float:
        if isinstance(value, bool):
            raise TypeError('value must be a Number, not a boolean.')
        else:
            return float(value)

    @classmethod
    def _serialize(cls, value: float) -> SerializedFloat:
        return value

    def __str__(self):
        return '<Float {!r}>'.format(self.serialization_path)


class Raw(Property[typing.Any, typing.Any]):

    @property
    def underlying_types(self):
        return object

    @property
    def serialized_types(self):
        return object

    @classmethod
    def _deserialize(cls, value: typing.Any) -> typing.Any:
        return value

    @classmethod
    def _serialize(cls, value: typing.Any) -> typing.Any:
        return value

    def __str__(self):
        return '<Raw {!r}>'.format(self.serialization_path)


class String(Property[str, str]):

    @property
    def underlying_types(self):
        return str

    @property
    def serialized_types(self):
        return str

    def _deserialize(self, value: str) -> str:
        value = self.default if value is None else value
        if value is None:
            raise ValueError('Value must not be none!')
        return str(value)

    def _serialize(self, value: str) -> str:
        return str(value)

    def __str__(self):
        return '<String {!r}>'.format(self.serialization_path)


class Boolean(Property[bool, bool]):

    @property
    def underlying_types(self):
        return bool

    @property
    def serialized_types(self):
        return bool

    def _deserialize(self, value: str) -> bool:
        return bool(value)

    def _serialize(self, value: str) -> bool:
        return bool(value)

    def __str__(self):
        return '<Boolean {!r}>'.format(self.serialization_path)


class UUID(Property[uuid.UUID, str]):

    @property
    def underlying_types(self):
        return uuid.UUID

    @property
    def serialized_types(self):
        return str

    def _deserialize(self, value: str) -> uuid.UUID:
        return uuid.UUID(value)

    def _serialize(self, value: uuid.UUID) -> str:
        return str(value)


class Datetime(Property[datetime, int]):

    @property
    def underlying_types(self):
        return datetime

    @property
    def serialized_types(self):
        return int, str

    def _deserialize(self, value) -> datetime:
        if isinstance(value, str):
            return arrow.get(value).datetime
        if isinstance(value, int):
            # Backend returns time as ms since epoch, but arrow expects seconds since epoch
            return arrow.get(value / 1000).datetime
        raise TypeError("{} must be an int or a string".format(value))

    def _serialize(self, value: datetime) -> int:
        return int(arrow.get(value).float_timestamp * 1000)


class List(PropertyCollection[list, list]):

    def __init__(self,
                 element_type: typing.Union[Property, typing.Type[Property]],
                 serialization_path: typing.Optional[str] = None,
                 *,
                 serializable: bool = True,
                 deserializable: bool = True,
                 default: typing.Optional[DeserializedType] = None,
                 override: bool = False,
                 use_init: bool = False
                 ):
        super().__init__(serialization_path=serialization_path,
                         serializable=serializable,
                         deserializable=deserializable,
                         default=default,
                         override=override,
                         use_init=use_init
                         )
        self.element_type = element_type if isinstance(element_type, Property) else element_type()

    @property
    def underlying_types(self):
        return list, set, tuple

    @property
    def serialized_types(self):
        return list

    def _deserialize(self, value: list) -> list:
        deserialized = []
        for element in value:
            deserialized.append(self.element_type.deserialize(element))
        return deserialized

    def _serialize(self, value: list) -> list:
        serialized = []
        for element in value:
            serialized.append(self.element_type.serialize(element))
        return serialized

    def _set_elements(self, value):
        elems = []
        for sub_val in value:
            if isinstance(self.element_type, PropertyCollection):
                val_to_append = self.element_type._set_elements(sub_val)
            elif issubclass(type(sub_val), self.element_type.underlying_types):
                val_to_append = sub_val
            else:
                val_to_append = self.element_type.deserialize(sub_val)
            elems.append(val_to_append)
        return elems


class Set(PropertyCollection[set, typing.Iterable]):

    def __init__(self,
                 element_type: typing.Union[Property, typing.Type[Property]],
                 serialization_path: typing.Optional[str] = None,
                 *,
                 serializable: bool = True,
                 deserializable: bool = True,
                 default: typing.Optional[DeserializedType] = None,
                 override: bool = False,
                 use_init: bool = False
                 ):
        super().__init__(serialization_path=serialization_path,
                         serializable=serializable,
                         deserializable=deserializable,
                         default=default,
                         override=override,
                         use_init=use_init)
        self.element_type = element_type if isinstance(element_type, Property) else element_type()

    @property
    def underlying_types(self):
        return set, list, tuple

    @property
    def serialized_types(self):
        return typing.Iterable

    def _deserialize(self, value: typing.Iterable) -> set:
        deserialized = set()
        for element in value:
            deserialized.add(self.element_type.deserialize(element))
        return deserialized

    def _serialize(self, value: set) -> list:
        serialized = list()
        for element in value:
            serialized.append(self.element_type.serialize(element))
        try:
            return sorted(serialized)
        except TypeError:
            return serialized

    def _set_elements(self, value):
        elems = set()
        for sub_val in value:
            if isinstance(self.element_type, PropertyCollection):
                val_to_append = self.element_type._set_elements(sub_val)
            elif issubclass(type(sub_val), self.element_type.underlying_types):
                val_to_append = sub_val
            else:
                val_to_append = self.element_type.deserialize(sub_val)
            elems.add(val_to_append)
        return elems


class Union(Property[typing.Any, typing.Any]):
    """
    One of several possible property types.

    Attempted de/serialization is done in the order in which types are provided in the constructor.
    """

    def __init__(self,
                 element_types: typing.Sequence[typing.Union[Property, typing.Type[Property]]],
                 serialization_path: typing.Optional[str] = None,
                 *,
                 serializable: bool = True,
                 deserializable: bool = True,
                 default: typing.Optional[DeserializedType] = None,
                 override: bool = False,
                 use_init: bool = False
                 ):
        super().__init__(serialization_path=serialization_path,
                         serializable=serializable,
                         deserializable=deserializable,
                         default=default,
                         override=override,
                         use_init=use_init)
        if not isinstance(element_types, typing.Iterable):
            raise ValueError("element types must be iterable: {}".format(element_types))
        self.element_types: typing.List[Property, ...] = \
            [el if isinstance(el, Property) else el() for el in element_types]

    @property
    def underlying_types(self):
        all_underlying_types = [prop.underlying_types for prop in self.element_types]
        return tuple(set(chain(*[typ if isinstance(typ, tuple)
                                 else (typ,) for typ in all_underlying_types])))

    @property
    def serialized_types(self):
        all_serialized_types = [prop.serialized_types for prop in self.element_types]
        return tuple(set(chain(*[typ if isinstance(typ, tuple)
                                 else (typ,) for typ in all_serialized_types])))

    def _serialize(self, value: typing.Any) -> typing.Any:
        for prop in self.element_types:
            try:
                return prop.serialize(value)
            except ValueError:
                pass
        raise ValueError("An unexpected error occurred while trying to serialize {} to one "
                         "of the following types: {}.".format(value, self.serialized_types))

    def _deserialize(self, value: typing.Any) -> typing.Any:
        for prop in self.element_types:
            try:
                return prop.deserialize(value)
            except ValueError:
                pass
        raise ValueError("An unexpected error occurred while trying to deserialize {} to "
                         "one of the following types: {}.".format(value, self.underlying_types))


class SpecifiedMixedList(PropertyCollection[list, list]):
    """A finite list in which the type of each entry is specified."""

    def __init__(self,
                 element_types: typing.Sequence[typing.Union[Property, typing.Type[Property]]],
                 serialization_path: typing.Optional[str] = None,
                 *,
                 serializable: bool = True,
                 deserializable: bool = True,
                 default: typing.Optional[DeserializedType] = None,
                 override: bool = False,
                 use_init: bool = False
                 ):
        super().__init__(serialization_path=serialization_path,
                         serializable=serializable,
                         deserializable=deserializable,
                         default=default,
                         override=override,
                         use_init=use_init)
        if not isinstance(element_types, list):
            raise ValueError("element types must be a list: {}".format(element_types))
        self.element_types: typing.List[Property, ...] = \
            [el if isinstance(el, Property) else el() for el in element_types]

    @property
    def underlying_types(self):
        return list, tuple

    @property
    def serialized_types(self):
        return list

    def _deserialize(self, value: list) -> tuple:
        if len(value) > len(self.element_types):
            raise ValueError("Cannot deserialize value {}, as it has more elements "
                             "than expected for list {}".format(value, self.element_types))
        deserialized = []
        for element, element_type in zip(value, self.element_types):
            deserialized.append(element_type.deserialize(element))

        # If there are more element types than elements, append default values
        for element_type in self.element_types[len(value):]:
            deserialized.append(element_type.default)

        return deserialized

    def _serialize(self, value: tuple) -> list:
        if len(value) > len(self.element_types):
            raise ValueError("Cannot serialize value {}, as it has more elements "
                             "than expected for list {}".format(value, self.element_types))
        serialized = []
        for element, element_type in zip(value, self.element_types):
            serialized.append(element_type.serialize(element))

        # If there are more element types than elements, append serialized default values
        for element_type in self.element_types[len(value):]:
            serialized.append(element_type.serialize(element_type.default))

        return serialized

    def _set_elements(self, value):
        elems = []
        if len(value) > len(self.element_types):
            raise ValueError("Cannot serialize value {}, as it has more elements "
                             "than expected for list {}".format(value, self.element_types))
        for element, element_type in zip(value, self.element_types):
            if isinstance(element_type, PropertyCollection):
                val_to_append = element_type._set_elements(element)
            elif issubclass(type(element), element_type.underlying_types):
                val_to_append = element
            else:
                val_to_append = element_type.deserialize(element)
            elems.append(val_to_append)

        # If there are more element types than elements, append serialized default values
        for element_type in self.element_types[len(value):]:
            elems.append(element_type.default)

        return elems


class Enumeration(Property[BaseEnumeration, str]):

    def __init__(self,
                 klass: typing.Type[typing.Any],
                 serialization_path: typing.Optional[str] = None,
                 *,
                 serializable: bool = True,
                 deserializable: bool = True,
                 default: typing.Optional[DeserializedType] = None,
                 override: bool = False,
                 use_init: bool = False
                 ):
        super().__init__(serialization_path=serialization_path,
                         serializable=serializable,
                         deserializable=deserializable,
                         default=default,
                         override=override,
                         use_init=use_init)
        self.klass = klass

    @property
    def underlying_types(self):
        return self.klass

    @property
    def serialized_types(self):
        return str

    def _deserialize(self, value: str) -> BaseEnumeration:
        return self.klass.from_str(value, exception=True)

    def _serialize(self, value: typing.Any) -> str:
        return self.klass.from_str(value, exception=True).value


@lru_cache(maxsize=1024)
def _fields_map(klass: typing.Type) -> typing.Dict[str, Property]:
    """Compute the properties-relevant fields in a given class."""
    return {
        k: v
        for x in reversed(klass.__mro__)  # Classes at the front trump
        for k, v in x.__dict__.items() if isinstance(v, Property)
    }


class Object(PropertyCollection[typing.Any, dict]):

    def __init__(self,
                 klass: typing.Type[typing.Any],
                 serialization_path: typing.Optional[str] = None,
                 *,
                 serializable: bool = True,
                 deserializable: bool = True,
                 default: typing.Optional[DeserializedType] = None,
                 override: bool = False,
                 use_init: bool = False
                 ):
        super().__init__(serialization_path=serialization_path,
                         serializable=serializable,
                         deserializable=deserializable,
                         default=default,
                         override=override,
                         use_init=use_init)
        self.klass = klass
        # We need to use __dict__ here because other access methods will invoke __get__
        self.fields: typing.Dict[str, Property] = _fields_map(self.klass)
        self.polymorphic = "get_type" in self.klass.__dict__ and\
                           issubclass(self.klass, PolymorphicSerializable)

    @property
    def underlying_types(self):
        return self.klass

    @property
    def serialized_types(self):
        return dict

    def _deserialize(self, data: dict) -> typing.Any:
        if self.polymorphic:
            return self.klass.get_type(data).build(data)
        if not self.fields:
            # Maybe there are no fields because we hit a gemd-python class
            if issubclass(self.klass, DictSerializable):
                return DictSerializable.build(data)
            raise AttributeError("Tried to deserialize to {!r}, which has no fields and is not an"
                                 " explicitly serializable class".format(self.klass))

        values = {}
        init_props = set()
        for property_name, field in self.fields.items():
            if field.use_init:
                init_props.add(property_name)
            if field.deserializable:
                values[property_name] = field.deserialize_from_dict(data)
            elif field.default is not None:
                values[property_name] = field.default

        if len(init_props) > 0:
            try:
                instance = self.klass(**{k: v for k, v in values.items() if k in init_props})
            except TypeError as e:
                # Check if it's because the signature was wrong
                sig = signature(self.klass.__init__)
                for arg, param in sig.parameters.items():
                    if arg not in init_props | {'self'}:
                        if param.default is param.empty:
                            raise AttributeError(
                                f"{self.klass} has at least 1 property marked as `use_init`, "
                                f"but required arguments weren't: {e}"
                            )
                else:
                    raise e
        else:
            instance = self.klass.__new__(self.klass)
        for property_name in values:
            if property_name not in init_props:
                setattr(instance, property_name, values[property_name])

        return instance

    def _serialize(self, obj: typing.Any) -> dict:
        serialized = {}
        if type(obj) != self.klass and isinstance(obj, Serializable):
            # If the object class doesn't match this one, then it is a subclass
            # that may have more fields, so defer to them by calling the dump method
            # it must have as a Serializable
            return obj.dump()
        if not self.fields:
            # There are two types of objects that we expect to not have fields.
            # One is a PolymorphicSerializable, which is handled above.
            # The other possibility is that obj is a gemd object that is not reproduced in
            # citrine-python (attribute, value, bounds, etc.). These are all DictSerializable,
            # and have a dump() method that uses the gemd json encoder client.
            try:
                return obj.dump()
            except AttributeError:
                raise AttributeError("Tried to serialize object {!r} of type {}, which has "
                                     "neither fields not a dump() method.".format(obj, type(obj)))
        for property_name, field in self.fields.items():
            if field.serializable:
                value = getattr(obj, property_name)
                serialized = field.serialize_to_dict(serialized, value)
        return serialized

    def __str__(self):
        return '<Object[{}] {!r}>'.format(self.klass.__name__, self.serialization_path)

    def _set_elements(self, value):
        if issubclass(type(value), self.klass):
            return value
        else:
            return self.deserialize(value)


class LinkOrElse(PropertyCollection[typing.Union[Serializable, LinkByUID], dict]):
    """
    A property that can either be a serializable object with IDs or a LinkByUID object.

    Serialization is done by converting the object to a dict. If it is a Serializable object
    it has a dump() method. LinkByUID has the as_dict() method.

    Deserialization to a LinkByUID is easy--it is constructed using value. Deserialization to
    a Serializable object is more difficult because this class does not know what object it is
    supposed to deserialize to (passing that information results in a circular import, because the
    objects that need to be deserialized in this use case have their own Property serde schema).
    Instead, we rely on the fact that all the Serializable classes with serde schema
    (data concepts objects, templates, etc.) know how to deserialize themselves through a
    build() method that doesn't call _deserialize().

    This is currently tied to LinkByUID in gemd, but could be modified to work with a
    generic Link object.
    """

    def __init__(self,
                 klass: typing.Type[typing.Any] = Serializable,
                 serialization_path: typing.Optional[str] = None,
                 *,
                 serializable: bool = True,
                 deserializable: bool = True,
                 default: typing.Optional[DeserializedType] = None,
                 override: bool = False,
                 use_init: bool = False
                 ):
        super().__init__(
            serialization_path=serialization_path,
            serializable=serializable,
            deserializable=deserializable,
            default=default,
            override=override,
            use_init=use_init)
        self.klass = klass

    @property
    def underlying_types(self):
        return self.klass, LinkByUID

    @property
    def serialized_types(self):
        return dict

    def _serialize(self, value: typing.Any) -> dict:
        if isinstance(value, LinkByUID):
            return value.as_dict()
        elif isinstance(value, Serializable):
            return value.dump()

    def _deserialize(self, value: dict):
        if 'type' in value:
            target = DictSerializable.class_mapping[value['type']]
            try:
                return target.build(value)
            except TypeError as e:
                # TODO: Consider migrating this ValueError to a TypeError for 3
                match = re.search(r"__init__.* missing (\d+) required \w+ arguments: (.+)", str(e))
                if match:
                    raise ValueError(
                        f"{match.group(1)} missing required "
                        f"field{'s' if match.group(1) != '1' else ''}: {match.group(2)}"
                    )
                else:
                    raise e
        raise Exception("Serializable object that is being pointed to must have a self-contained "
                        "build() method that does not call deserialize().")

    def _set_elements(self, value):
        return value


class Optional(PropertyCollection[typing.Optional[typing.Any], typing.Optional[typing.Any]]):

    def __init__(self,
                 prop: typing.Union[Property, typing.Type[Property]],
                 serialization_path: typing.Optional[str] = None,
                 *,
                 serializable: bool = True,
                 deserializable: bool = True,
                 default: typing.Optional[DeserializedType] = None,
                 override: bool = False,
                 use_init: bool = False
                 ):
        super().__init__(serialization_path=serialization_path,
                         serializable=serializable,
                         deserializable=deserializable,
                         default=default,
                         override=override,
                         use_init=use_init)
        self.prop = prop if isinstance(prop, Property) else prop()
        self.optional = True

    @property
    def underlying_types(self):
        constituent_types = self.prop.underlying_types
        if isinstance(constituent_types, tuple):
            return constituent_types + (type(None),)
        else:
            return constituent_types, type(None)

    @property
    def serialized_types(self):
        constituent_types = self.prop.serialized_types
        if isinstance(constituent_types, tuple):
            return constituent_types + (type(None),)
        else:
            return constituent_types, type(None)

    def _deserialize(self, data: typing.Optional[typing.Any]) -> typing.Optional[typing.Any]:
        return self.prop.deserialize(data) if data is not None else None

    def _serialize(self, obj: typing.Optional[typing.Any]) -> typing.Optional[typing.Any]:
        return self.prop.serialize(obj) if obj is not None else None

    def __str__(self):
        return '<Optional[{}] {!r}>'.format(self.prop, self.serialization_path)

    def _set_elements(self, value):
        elem = None
        if value is not None:
            if isinstance(self.prop, PropertyCollection):
                elem = self.prop._set_elements(value)
            else:
                elem = value
        return elem


class Mapping(PropertyCollection[dict, dict]):
    """
    Serialization of a Mapping.

    Serialization is done by converting the map to a dict by default, serializing the
    keys and the values.

    If the optional parameter `ser_as_list_of_pairs` is set to True, serialization is done
    by converting the map to a list of key value pairs. Deserialization expects a list of
    key value pairs and converts them to a dict.
    """

    def __init__(self,
                 keys_type: typing.Union[Property, typing.Type[Property]],
                 values_type: typing.Union[Property, typing.Type[Property]],
                 serialization_path: typing.Optional[str] = None,
                 *,
                 serializable: bool = True,
                 deserializable: bool = True,
                 default: typing.Optional[dict] = None,
                 override: bool = False,
                 use_init: bool = False,
                 ser_as_list_of_pairs: bool = False):
        super().__init__(serialization_path=serialization_path,
                         serializable=serializable,
                         deserializable=deserializable,
                         default=default,
                         override=override,
                         use_init=use_init
                         )

        self.keys_type = keys_type if isinstance(keys_type, Property) else keys_type()
        self.values_type = values_type if isinstance(values_type, Property) else values_type()
        self.ser_as_list_of_pairs = ser_as_list_of_pairs

    @property
    def underlying_types(self):
        return dict

    @property
    def serialized_types(self):
        if self.ser_as_list_of_pairs:
            return list
        else:
            return dict

    def _deserialize(self, value: typing.Union[dict, list]) -> dict:
        deserialized = dict()

        if type(value) == list:
            for pair in value:
                deserialized_key = self.keys_type.deserialize(pair[0])
                deserialized_value = self.values_type.deserialize(pair[1])
                deserialized[deserialized_key] = deserialized_value
            return deserialized

        for key, value in value.items():
            deserialized_key = self.keys_type.deserialize(key)
            deserialized_value = self.values_type.deserialize(value)
            deserialized[deserialized_key] = deserialized_value
        return deserialized

    def _serialize(self, value: dict) -> typing.Union[dict, list]:
        if self.ser_as_list_of_pairs:
            serialized = []
            for key, value in value.items():
                serialized_key = self.keys_type.serialize(key)
                serialized_value = self.values_type.serialize(value)
                serialized.append((serialized_key, serialized_value))
            return serialized

        serialized = dict()
        for key, value in value.items():
            serialized_key = self.keys_type.serialize(key)
            serialized_value = self.values_type.serialize(value)
            serialized[serialized_key] = serialized_value
        return serialized

    def _set_elements(self, value):
        elems = dict()
        for key, val in value.items():
            if isinstance(self.values_type, PropertyCollection):
                deserialized_value = self.values_type._set_elements(val)
            elif issubclass(type(val), self.values_type.underlying_types):
                deserialized_value = val
            else:
                deserialized_value = self.values_type.deserialize(val)

            if isinstance(self.keys_type, PropertyCollection):
                deserialized_key = self.keys_type._set_elements(key)
            elif issubclass(type(key), self.keys_type.underlying_types):
                deserialized_key = key
            else:
                deserialized_key = self.keys_type.deserialize(key)

            elems[deserialized_key] = deserialized_value
        return elems
