import uuid
import arrow
from citrine._serialization import properties


VALID_SERIALIZATIONS = [
    (properties.Integer, 5, 5),
    (properties.Float, 3.0, 3.0),
    (properties.Raw, 1234, 1234),
    (properties.String, 'foo', 'foo'),
    (properties.Boolean, True, True),
    (properties.Boolean, False, False),
    (properties.UUID, uuid.UUID('284e6cec-dd05-4f8e-9a94-4abb298bde82'), '284e6cec-dd05-4f8e-9a94-4abb298bde82'),
    (properties.Datetime, arrow.get(269815509154).datetime, 269815509154),
    (properties.Datetime, arrow.get('2019-07-19T10:46:08+00:00').datetime, 1563533168000),
]


INVALID_DESERIALIZATION_TYPES = [
    (properties.Integer, object()),
    (properties.Float, object()),
    (properties.String, 1),
    (properties.Boolean, 3),
    (properties.Boolean, 'False'),
    (properties.UUID, '284e6cec'),
]


class DummyProperty(properties.Property):
    """This is a concrete sublcass that does not overwrite __str__ for base Property testing"""
    @property
    def underlying_types(self):
        return None

    @property
    def serialized_types(self):
        return None

    def _serialize(self, value):
        pass

    def _deserialize(self, value):
        pass


VALID_STRINGS = [
    (DummyProperty, 'hi', "<Property 'hi'>"),
    (properties.Raw, 'hi', "<Raw 'hi'>"),
    (properties.Integer, 'foo', "<Integer 'foo'>"),
    (properties.Float, 'bar', "<Float 'bar'>"),
    (properties.String, 'foobar', "<String 'foobar'>"),
    (properties.Boolean, 'what', "<Boolean 'what'>"),
]

INVALID_INSTANCES = [
    (properties.Integer, 1.0),  # float != int
    (properties.Integer, "1"),
    (properties.Integer, complex(1, 2)),
    (properties.Integer, True),
    (properties.Integer, 'asdf'),
    (properties.Float, complex(1, 2)),
    (properties.Float, True),
    (properties.Float, 'asdf'),
    (properties.String, 1),
    (properties.String, dict()),
    (properties.Boolean, 1),
    (properties.Boolean, 1.0),
    (properties.Boolean, 'asdf'),
    (properties.UUID, str(uuid.uuid4())),  # string(uuid) != uuid
    (properties.UUID, 1.0),
    (properties.Datetime, '2019-07-19T10:46:08.949682+00:00'),  # str(datetime) != datetime
    (properties.LinkOrElse, object())
]

INVALID_SERIALIZED_INSTANCES = [
    (properties.Integer, '1.0'),
    (properties.Integer, str(complex(1, 2))),
    (properties.Integer, True),
    (properties.Integer, 'asdf'),
    (properties.Integer, 14.4),
    (properties.Float, str(complex(1,2))),
    (properties.Float, True),
    (properties.Float, 'asdf'),
    (properties.String, 1),
    (properties.String, dict()),
    (properties.Boolean, 1),
    (properties.Boolean, 1.0),
    (properties.Boolean, 'asdf'),
    (properties.UUID, 'wrong-number-of-chars'),
    (properties.Datetime, '2019-07-19T35:46:08.949682+99:99'),  # nonsense time
]
