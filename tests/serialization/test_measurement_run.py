"""Tests of the Measurement Run schema"""
import pytest
from uuid import uuid4

from citrine.attributes.property import Property
from taurus.entity.value.nominal_integer import NominalInteger
from citrine.resources.measurement_run import MeasurementRun
from citrine.resources.material_run import MaterialRun
from citrine.resources.audit_info import AuditInfo


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        uids={'id': str(uuid4())},
        name='Taste test',
        tags=[],
        notes=None,
        conditions=[],
        parameters=[],
        properties=[{'name': 'sweetness', 'type': 'property', 'template': None, 'notes': None,
                     'origin': 'measured', 'file_links': [],
                     'value': {'type': 'nominal_integer', 'nominal': 7}},
                    {'type': 'property', 'name': 'fluffiness', 'template': None, 'notes': None,
                     'origin': 'measured', 'file_links': [],
                     'value': {'type': 'nominal_integer', 'nominal': 10}
                     }],
        material={
            'uids': {'id': str(uuid4())},
            'name': 'sponge cake',
            'tags': [],
            'notes': None,
            'process': None,
            'sample_type': 'experimental',
            'spec': None,
            'file_links': [],
            'type': 'material_run',
            'audit_info': {
                'created_by': 'user1', 'created_at': 1559933807392,
                'updated_by': 'user2', 'updated_at': 1560033807392
            }
        },
        spec=None,
        file_links=[],
        type='measurement_run',
        source={
            "type": "performed_source",
            "performed_by": "Marie Curie",
            "performed_date": "1898-07-01"
        },
        audit_info={'created_by': 'user2', 'created_at': 1560033807392}
    )


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized Measurement Run looks sane."""
    measurement_run: MeasurementRun = MeasurementRun.build(valid_data)
    assert measurement_run.uids == {'id': valid_data['uids']['id']}
    assert measurement_run.name == 'Taste test'
    assert measurement_run.notes is None
    assert measurement_run.tags == []
    assert measurement_run.conditions == []
    assert measurement_run.parameters == []
    assert measurement_run.properties[0] == Property('sweetness', origin="measured",
                                                            value=NominalInteger(7))
    assert measurement_run.properties[1] == Property('fluffiness', origin="measured",
                                                            value=NominalInteger(10))
    assert measurement_run.file_links == []
    assert measurement_run.template is None
    assert measurement_run.material == MaterialRun('sponge cake',
                                                   uids={'id': valid_data['material']['uids']['id']},
                                                   sample_type='experimental')
    assert measurement_run.material.audit_info == AuditInfo(**valid_data['material']['audit_info'])
    assert measurement_run.spec is None
    assert measurement_run.typ == 'measurement_run'
    assert measurement_run.audit_info == AuditInfo(**valid_data['audit_info'])


def test_serialization(valid_data):
    """Ensure that a serialized Measurement Run looks sane."""
    measurement_run: MeasurementRun = MeasurementRun.build(valid_data)
    serialized = measurement_run.dump()
    valid_data['material'].pop('audit_info')
    valid_data.pop('audit_info')
    assert serialized == valid_data


def test_material_attachment():
    """Test that a material can be attached to a measurement, and the connection survives serde."""
    cake = MaterialRun('Final Cake')
    mass = MeasurementRun('Weigh cake', material=cake)
    mass_data = mass.dump()
    mass_copy = MeasurementRun.build(mass_data)
    assert mass_copy == mass
