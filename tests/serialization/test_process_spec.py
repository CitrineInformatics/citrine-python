"""Tests of the Process Run schema"""
import pytest
from uuid import uuid4

from taurus.entity.attribute.parameter import Parameter
from taurus.entity.bounds.real_bounds import RealBounds
from taurus.entity.value.uniform_real import UniformReal
from taurus.entity.file_link import FileLink
from citrine.resources.process_spec import ProcessSpec
from citrine.resources.process_template import ProcessTemplate
from citrine.resources.parameter_template import ParameterTemplate
from citrine.resources.audit_info import AuditInfo


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        uids={'id': str(uuid4())},
        name='Process 1',
        tags=['baking::cakes', 'danger::low'],
        notes='make sure to use oven mitts',
        parameters=[{'name': 'oven temp', 'type': 'parameter',
                     'template': None, 'origin': 'specified', 'notes': None, 'file_links': [],
                     'value': {'lower_bound': 195, 'upper_bound': 205,
                               'units': 'dimensionless', 'type': 'uniform_real'}
                     }],
        conditions=[],
        template={
            'name': 'the template',
            'uids': {'id': str(uuid4())},
            'type': 'process_template',
            'conditions': [],
            'parameters': [
                [
                    {
                        'type': 'parameter_template',
                        'name': 'oven temp template',
                        'bounds': {'type': 'real_bounds', 'lower_bound': 175, 'upper_bound': 225, 'default_units': 'dimensionless'},
                        'uids': {'id': str(uuid4())},
                        'description': None, 'tags': []
                    },
                    {
                        'type': 'real_bounds',
                        'lower_bound': 175, 'upper_bound': 225, 'default_units': 'dimensionless'
                    }
                ]
            ],
            'allowed_labels': ['a', 'b'],
            'allowed_names': ['a name'],
            'description': 'a long description',
            'tags': []
        },
        file_links=[{'type': 'file_link', 'filename': 'cake_recipe.txt', 'url': 'www.baking.com'}],
        audit_info={'created_by': str(uuid4()), 'created_at': 1559933807392},
        type='process_spec'
    )


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized Process Spec looks sane."""
    process_spec: ProcessSpec = ProcessSpec.build(valid_data)
    assert process_spec.uids == {'id': valid_data['uids']['id']}
    assert process_spec.tags == ['baking::cakes', 'danger::low']
    assert process_spec.parameters[0] == Parameter(name='oven temp',
                                                          value=UniformReal(195, 205, ''),
                                                          origin='specified')
    assert process_spec.conditions == []
    assert process_spec.template == \
           ProcessTemplate('the template', uids={'id': valid_data['template']['uids']['id']},
                           parameters=[
                               [ParameterTemplate('oven temp template',
                                                  bounds=RealBounds(175, 225, ''),
                                                  uids={'id': valid_data['template']['parameters'][0][0]['uids']['id']}),
                                RealBounds(175, 225, '')]
                           ],
                           description='a long description',
                           allowed_labels=['a', 'b'],
                           allowed_names=['a name'])
    assert process_spec.name == 'Process 1'
    assert process_spec.notes == 'make sure to use oven mitts'
    assert process_spec.file_links == [FileLink('cake_recipe.txt', 'www.baking.com')]
    assert process_spec.typ == 'process_spec'
    assert process_spec.audit_info == AuditInfo(**valid_data['audit_info'])


def test_serialization(valid_data):
    """Ensure that a serialized Process Run looks sane."""
    process_spec: ProcessSpec = ProcessSpec.build(valid_data)
    serialized = process_spec.dump()
    valid_data.pop('audit_info')  # this field is not serialized
    assert serialized == valid_data
