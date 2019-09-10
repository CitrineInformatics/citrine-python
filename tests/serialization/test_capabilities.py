"""Tests for citrine.informatics.capabilities serialization."""
import uuid

import pytest

from citrine.informatics.capabilities import Capability, ProductCapability
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension


@pytest.fixture
def valid_data():
    """Produce valid capability data."""
    return dict(
        status='VALIDATING',
        status_info=None,
        display_name='my capability',
        schema_id='6c16d694-d015-42a7-b462-8ef299473c9a',
        id=str(uuid.uuid4()),
        config=dict(
            type='Univariate',
            name='my capability',
            description='does some things',
            dimensions=[
                dict(
                    type='ContinuousDimension',
                    template_id=str(uuid.uuid4()),
                    descriptor=dict(
                        type='Real',
                        descriptor_key='alpha',
                        units='',
                        lower_bound=5.0,
                        upper_bound=10.0,
                    ),
                    lower_bound=6.0,
                    upper_bound=7.0
                ),
                dict(
                    type='EnumeratedDimension',
                    template_id=str(uuid.uuid4()),
                    descriptor=dict(
                        type='Categorical',
                        descriptor_key='color',
                        descriptor_values=['red', 'green', 'blue'],
                    ),
                    list=['red']
                )
            ]
        )
    )


@pytest.fixture
def valid_serialization_output(valid_data):
    return {x: y for x, y in valid_data.items() if x not in ['status', 'status_info']}


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized ProductCapability looks sane."""
    capability: ProductCapability = ProductCapability.build(valid_data)
    assert capability.name == 'my capability'
    assert capability.description == 'does some things'
    assert type(capability.dimensions[0]) == ContinuousDimension
    assert capability.dimensions[0].lower_bound == 6.0
    assert type(capability.dimensions[1]) == EnumeratedDimension
    assert capability.dimensions[1].values == ['red']


def test_polymorphic_deserialization(valid_data):
    """Ensure that a polymorphically deserialized ProductCapability looks sane."""
    capability: ProductCapability = Capability.build(valid_data)
    assert capability.name == 'my capability'
    assert capability.description == 'does some things'
    assert type(capability.dimensions[0]) == ContinuousDimension
    assert capability.dimensions[0].lower_bound == 6.0
    assert type(capability.dimensions[1]) == EnumeratedDimension
    assert capability.dimensions[1].values == ['red']


def test_serialization(valid_data, valid_serialization_output):
    """Ensure that a serialized ProductCapability looks sane."""
    capability = ProductCapability.build(valid_data)
    serialized = capability.dump()
    serialized['id'] = valid_data['id']
    assert serialized == valid_serialization_output
