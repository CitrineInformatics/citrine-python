"""Tests of the material spec schema."""
import pytest
from uuid import uuid4

from citrine.resources.material_spec import MaterialSpec
from gemd.entity.attribute.condition import Condition
from gemd.entity.attribute.property import Property
from gemd.entity.attribute.property_and_conditions import PropertyAndConditions
from gemd.entity.value.nominal_categorical import NominalCategorical
from gemd.entity.value.nominal_real import NominalReal


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        name='spec of material',
        uids={'id': str(uuid4())},
        tags=[],
        notes=None,
        process=None,
        template=None,
        properties=[
            {
                'type': 'property_and_conditions',
                'property':
                    {
                        'type': 'property',
                        'origin': 'specified',
                        'name': 'color',
                        'template': None,
                        'notes': None,
                        'value': {'category': 'tan', 'type': 'nominal_categorical'},
                        'file_links': []
                    },
                'conditions':
                    [
                         {
                             'type': 'condition',
                             'origin': 'specified',
                             'name': 'temperature',
                             'template': None,
                             'notes': None,
                             'value': {
                                 'type': 'nominal_real',
                                 'nominal': 300.0,
                                 'units': 'kelvin'
                             },
                             'file_links': []
                         }
                     ]
            }
        ],
        file_links=[],
        type='material_spec'
    )


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized Material Spec looks sane."""
    material_spec: MaterialSpec = MaterialSpec.build(valid_data)
    assert material_spec.uids == {'id': valid_data['uids']['id']}
    assert material_spec.name == 'spec of material'
    assert material_spec.tags == []
    assert material_spec.notes is None
    assert material_spec.process is None
    assert material_spec.properties[0] == \
        PropertyAndConditions(Property("color", origin='specified',
                                       value=NominalCategorical("tan")),
                              conditions=[Condition('temperature', origin='specified',
                                                    value=NominalReal(300, units='kelvin'))])
    assert material_spec.template is None
    assert material_spec.file_links == []
    assert material_spec.typ == 'material_spec'


def test_serialization(valid_data):
    """Ensure that a serialized Material Run looks sane."""
    material_spec: MaterialSpec = MaterialSpec.build(valid_data)
    serialized = material_spec.dump()
    assert serialized == valid_data
