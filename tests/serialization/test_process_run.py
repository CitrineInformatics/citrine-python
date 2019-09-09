"""Tests of the Process Run schema"""
import pytest
from uuid import uuid4

from taurus.entity.value.nominal_real import NominalReal
from taurus.entity.value.uniform_real import UniformReal
from citrine.attributes.condition import Condition
from citrine.resources.process_run import ProcessRun
from citrine.resources.process_spec import ProcessSpec


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        uids={'id': str(uuid4()), 'my_id': 'process1-v1'},
        name='Process 1',
        tags=['baking::cakes', 'danger::low'],
        notes='make sure to use oven mitts',
        conditions=[{'name': 'oven temp', 'type': 'condition', 'notes': None,
                     'template': None, 'origin': 'measured', 'file_links': [],
                     'value': {'nominal': 203.0, 'units': 'dimensionless', 'type': 'nominal_real'}
                     }],
        parameters=[],
        ingredients=[],
        spec={'type': 'process_spec', 'name': 'Spec for proc 1',
              'uids': {'id': str(uuid4())}, 'file_links': [], 'notes': None,
              'conditions': [{'type': 'condition', 'name': 'oven temp', 'origin': 'specified',
                              'template': None, 'notes': None, 'file_links': [],
                              'value': {'type': 'uniform_real', 'units': 'dimensionless',
                                        'lower_bound': 175, 'upper_bound': 225
                                        }
                              }],
              'template': None, 'tags': [], 'parameters': [], 'ingredients': []
              },
        file_links=[],
        type='process_run'
    )


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized Process Run looks sane."""
    process_run: ProcessRun = ProcessRun.build(valid_data)
    assert process_run.uids == {'id': valid_data['uids']['id'], 'my_id': 'process1-v1'}
    assert process_run.tags == ['baking::cakes', 'danger::low']
    assert process_run.conditions[0] == Condition(name='oven temp',
                                                         value=NominalReal(203.0, ''),
                                                         origin='measured')
    assert process_run.parameters == []
    assert process_run.ingredients == []
    assert process_run.file_links == []
    assert process_run.template is None
    assert process_run.output_material is None
    assert process_run.spec == \
           ProcessSpec(name="Spec for proc 1",
                       uids={'id': valid_data['spec']['uids']['id']},
                       conditions=[Condition(name='oven temp', value=UniformReal(175, 225, ''),
                                             origin='specified')]
                       )
    assert process_run.name == 'Process 1'
    assert process_run.notes == 'make sure to use oven mitts'
    assert process_run.typ == 'process_run'


def test_serialization(valid_data):
    """Ensure that a serialized Process Run looks sane."""
    process_run: ProcessRun = ProcessRun.build(valid_data)
    serialized = process_run.dump()
    assert serialized == valid_data
