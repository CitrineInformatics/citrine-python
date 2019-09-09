"""Tests of attributes."""
import pytest
from uuid import uuid4

from citrine.resources.property_template import PropertyTemplate
from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.parameter_template import ParameterTemplate
from citrine.attributes.property import Property
from citrine.attributes.condition import Condition
from citrine.attributes.parameter import Parameter
from taurus.entity.bounds.real_bounds import RealBounds
from taurus.entity.value.nominal_real import NominalReal

@pytest.fixture
def valid_data():
    """Return valid data of a serialized property."""
    return dict(
        name='mass',
        notes='This is a note',
        value={
            'type': 'nominal_real',
            'nominal': 5.0,
            'units': 'gram'
        },
        file_links=[],
        template={
            'type': 'dummy',
            'name': 'mass',
            'description': 'mass of object',
            'uids': {'id': str(uuid4())},
            'tags': [],
            'bounds': {
                'type': 'real_bounds',
                'lower_bound': 0.0,
                'upper_bound': 20.0,
                'default_units': 'gram'
            }
        },
        origin='measured',
        type='dummy'
    )


@pytest.fixture()
def attribute_list():
    """Return a list of tuples (key, attribute class, attribute template class)"""
    return [('property', Property, PropertyTemplate),
            ('condition', Condition, ConditionTemplate),
            ('parameter', Parameter, ParameterTemplate)]


def test_simple_deserialization(valid_data, attribute_list):
    for (key, Attribute, AttributeTemplate) in attribute_list:
        valid_data['type'] = key
        valid_data['template']['type'] = key + '_template'
        attribute: Attribute = Attribute.build(valid_data)
        assert attribute.name == 'mass'
        assert attribute.notes == 'This is a note'
        assert attribute.value == NominalReal(5.0, units='gram')
        assert attribute.template == \
               AttributeTemplate('mass', uids={'id': valid_data['template']['uids']['id']},
                                 description='mass of object', bounds=RealBounds(0.0, 20.0, 'gram')
                                 )
        assert attribute.origin == 'measured'
        assert attribute.file_links == []
        assert attribute.typ == key


def test_serialization(valid_data, attribute_list):
    for (key, Attribute, AttributeTemplate) in attribute_list:
        valid_data['type'] = key
        valid_data['template']['type'] = key + '_template'
        attribute: Attribute = Attribute.build(valid_data)
        serialized = attribute.dump()
        assert serialized == valid_data
