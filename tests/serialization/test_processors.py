"""Tests for citrine.informatics.processors serialization."""
import uuid
import pytest

from citrine.informatics.processors import Processor, GridProcessor, EnumeratedProcessor


@pytest.fixture
def valid_grid_data():
    """Valid GridProcessor data."""
    return dict(
        module_type='PROCESSOR',
        status='READY',
        status_info=['Things are looking good'],
        display_name='my processor',
        schema_id='272791a5-5468-4344-ac9f-2811d9266a4d',
        id=str(uuid.uuid4()),
        config=dict(
            type='Grid',
            name='my processor',
            description='does some things',
            grid_dimensions=dict(x=5, y=10),
        )
    )


@pytest.fixture
def valid_enumerated_data():
    """Valid EnumeratedProcessor data."""
    return dict(
        module_type='PROCESSOR',
        status='READY',
        status_info=['valid'],
        display_name='my enumerated processor',
        schema_id='272791a5-5468-4344-ac9f-2811d9266a4d',
        id=str(uuid.uuid4()),
        config=dict(
            type='Enumerated',
            name='my enumerated processor',
            description='enumerates all the things',
            max_size=10,
        )
    )


def valid_serialization_output(valid_grid_data):
    return { x: y for x, y in valid_grid_data.items() if x not in ['status', 'status_info']}


def test_simple_grid_deserialization(valid_grid_data):
    """Ensure a deserialized GridProcessor looks sane."""
    processor: GridProcessor = GridProcessor.build(valid_grid_data)
    assert processor.name == 'my processor'
    assert processor.description == 'does some things'
    assert processor.grid_sizes == dict(x=5, y=10)


def test_polymorphic_grid_deserialization(valid_grid_data):
    """Ensure a polymorphically deserialized GridProcessor looks sane."""
    processor: GridProcessor = Processor.build(valid_grid_data)
    assert processor.name == 'my processor'
    assert processor.description == 'does some things'
    assert processor.grid_sizes == dict(x=5, y=10)


def test_grid_serialization(valid_grid_data):
    """Ensure a serialized GridProcessor looks sane."""
    processor: GridProcessor = GridProcessor.build(valid_grid_data)
    serialized = processor.dump()
    serialized['id'] = valid_grid_data['id']
    assert serialized == valid_serialization_output(valid_grid_data)


def test_simple_enumerated_deserialization(valid_enumerated_data):
    """Ensure a deserialized EnumeratedProcessor looks sane."""
    processor: EnumeratedProcessor = EnumeratedProcessor.build(valid_enumerated_data)
    assert processor.name == 'my enumerated processor'
    assert processor.description == 'enumerates all the things'
    assert processor.max_size == 10


def test_polymorphic_enumerated_deserialization(valid_enumerated_data):
    """Ensure a polymorphically deserialized EnumeratedProcessor looks sane."""
    processor: EnumeratedProcessor = Processor.build(valid_enumerated_data)
    assert processor.name == 'my enumerated processor'
    assert processor.description == 'enumerates all the things'
    assert processor.max_size == 10


def test_enumerated_serialization(valid_enumerated_data):
    """Ensure a serialized EnumeratedProcessor looks sane."""
    processor: EnumeratedProcessor = EnumeratedProcessor.build(valid_enumerated_data)
    serialized = processor.dump()
    serialized['id'] = valid_enumerated_data['id']
    assert serialized == valid_serialization_output(valid_enumerated_data)
