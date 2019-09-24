"""Tests for citrine.informatics.design_spaces serialization."""
import uuid

import pytest

from citrine.informatics.descriptors import CategoricalDescriptor, RealDescriptor
from citrine.informatics.design_spaces import DesignSpace, ProductDesignSpace, EnumeratedDesignSpace
from citrine.informatics.dimensions import ContinuousDimension, EnumeratedDimension


@pytest.fixture
def valid_product_data():
    """Produce valid product design space data."""
    return dict(
        module_type='DESIGN_SPACE',
        status='VALIDATING',
        status_info=None,
        display_name='my design space',
        schema_id='6c16d694-d015-42a7-b462-8ef299473c9a',
        id=str(uuid.uuid4()),
        config=dict(
            type='Univariate',
            name='my design space',
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
def valid_enumerated_data():
    """Produce valid enumerated design space data."""
    return dict(
        module_type='DESIGN_SPACE',
        status='VALIDATING',
        status_info=None,
        display_name='my enumerated design space',
        schema_id='f3907a58-aa46-462c-8837-a5aa9605e79e',
        id=str(uuid.uuid4()),
        config=dict(
            type='EnumeratedDesignSpace',
            name='my enumerated design space',
            description='enumerates some things',
            descriptors=[
                dict(
                    type='Real',
                    descriptor_key='x',
                    units='',
                    lower_bound=1.0,
                    upper_bound=2.0,
                ),
                dict(
                    type='Categorical',
                    descriptor_key='color',
                    descriptor_values=['red', 'green', 'blue'],
                )
            ],
            data=[
                dict(x=1, color='red'),
                dict(x=2.0, color='green')
            ]
        )
    )


def valid_serialization_output(valid_data):
    return {x: y for x, y in valid_data.items() if x not in ['status', 'status_info']}


def test_simple_product_deserialization(valid_product_data):
    """Ensure that a deserialized ProductDesignSpace looks sane."""
    design_space: ProductDesignSpace = ProductDesignSpace.build(valid_product_data)
    assert design_space.name == 'my design space'
    assert design_space.description == 'does some things'
    assert type(design_space.dimensions[0]) == ContinuousDimension
    assert design_space.dimensions[0].lower_bound == 6.0
    assert type(design_space.dimensions[1]) == EnumeratedDimension
    assert design_space.dimensions[1].values == ['red']


def test_polymorphic_product_deserialization(valid_product_data):
    """Ensure that a polymorphically deserialized ProductDesignSpace looks sane."""
    design_space: ProductDesignSpace = DesignSpace.build(valid_product_data)
    assert design_space.name == 'my design space'
    assert design_space.description == 'does some things'
    assert type(design_space.dimensions[0]) == ContinuousDimension
    assert design_space.dimensions[0].lower_bound == 6.0
    assert type(design_space.dimensions[1]) == EnumeratedDimension
    assert design_space.dimensions[1].values == ['red']


def test_product_serialization(valid_product_data):
    """Ensure that a serialized ProductDesignSpace looks sane."""
    design_space = ProductDesignSpace.build(valid_product_data)
    serialized = design_space.dump()
    serialized['id'] = valid_product_data['id']
    assert serialized == valid_serialization_output(valid_product_data)


def test_simple_enumerated_deserialization(valid_enumerated_data):
    """Ensure that a deserialized EnumeratedDesignSpace looks sane."""
    design_space: EnumeratedDesignSpace = EnumeratedDesignSpace.build(valid_enumerated_data)
    assert design_space.name == 'my enumerated design space'
    assert design_space.description == 'enumerates some things'

    assert len(design_space.descriptors) == 2

    real, categorical = design_space.descriptors

    assert type(real) == RealDescriptor
    assert real.key == 'x'
    assert real.units == ''
    assert real.lower_bound == 1.0
    assert real.upper_bound == 2.0

    assert type(categorical) == CategoricalDescriptor
    assert categorical.key == 'color'
    assert categorical.categories == ['red', 'green', 'blue']

    assert len(design_space.data) == 2
    assert design_space.data[0] == {'x': 1.0, 'color': 'red'}
    assert design_space.data[1] == {'x': 2.0, 'color': 'green'}


def test_polymorphic_enumerated_deserialization(valid_enumerated_data):
    """Ensure that a polymorphically deserialized EnumeratedDesignSpace looks sane."""
    design_space: EnumeratedDesignSpace = DesignSpace.build(valid_enumerated_data)
    assert design_space.name == 'my enumerated design space'
    assert design_space.description == 'enumerates some things'

    assert len(design_space.descriptors) == 2

    real, categorical = design_space.descriptors

    assert type(real) == RealDescriptor
    assert real.key == 'x'
    assert real.units == ''
    assert real.lower_bound == 1.0
    assert real.upper_bound == 2.0

    assert type(categorical) == CategoricalDescriptor
    assert categorical.key == 'color'
    assert categorical.categories == ['red', 'green', 'blue']

    assert len(design_space.data) == 2
    assert design_space.data[0] == {'x': 1.0, 'color': 'red'}
    assert design_space.data[1] == {'x': 2.0, 'color': 'green'}


def test_enumerated_serialization(valid_enumerated_data):
    """Ensure that a serialized EnumeratedDesignSpace looks sane."""
    design_space = EnumeratedDesignSpace.build(valid_enumerated_data)
    serialized = design_space.dump()
    serialized['id'] = valid_enumerated_data['id']
    assert serialized == valid_serialization_output(valid_enumerated_data)
