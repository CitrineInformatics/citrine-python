"""Tests for citrine.informatics.processors serialization."""
from citrine.informatics.processors import Processor, GridProcessor, EnumeratedProcessor


def valid_serialization_output(valid_grid_processor_data):
    return { x: y for x, y in valid_grid_processor_data.items() if x not in ['status', 'status_info']}


def test_simple_grid_deserialization(valid_grid_processor_data):
    """Ensure a deserialized GridProcessor looks sane."""
    processor: GridProcessor = GridProcessor.build(valid_grid_processor_data)
    assert processor.name == 'my processor'
    assert processor.description == 'does some things'
    assert processor.grid_sizes == dict(x=5, y=10)


def test_polymorphic_grid_deserialization(valid_grid_processor_data):
    """Ensure a polymorphically deserialized GridProcessor looks sane."""
    processor: GridProcessor = Processor.build(valid_grid_processor_data)
    assert processor.name == 'my processor'
    assert processor.description == 'does some things'
    assert processor.grid_sizes == dict(x=5, y=10)


def test_grid_serialization(valid_grid_processor_data):
    """Ensure a serialized GridProcessor looks sane."""
    processor: GridProcessor = GridProcessor.build(valid_grid_processor_data)
    serialized = processor.dump()
    serialized['id'] = valid_grid_processor_data['id']
    assert serialized == valid_serialization_output(valid_grid_processor_data)


def test_simple_enumerated_deserialization(valid_enumerated_processor_data):
    """Ensure a deserialized EnumeratedProcessor looks sane."""
    processor: EnumeratedProcessor = EnumeratedProcessor.build(valid_enumerated_processor_data)
    assert processor.name == 'my enumerated processor'
    assert processor.description == 'enumerates all the things'
    assert processor.max_size == 10


def test_polymorphic_enumerated_deserialization(valid_enumerated_processor_data):
    """Ensure a polymorphically deserialized EnumeratedProcessor looks sane."""
    processor: EnumeratedProcessor = Processor.build(valid_enumerated_processor_data)
    assert processor.name == 'my enumerated processor'
    assert processor.description == 'enumerates all the things'
    assert processor.max_size == 10


def test_enumerated_serialization(valid_enumerated_processor_data):
    """Ensure a serialized EnumeratedProcessor looks sane."""
    processor: EnumeratedProcessor = EnumeratedProcessor.build(valid_enumerated_processor_data)
    serialized = processor.dump()
    serialized['id'] = valid_enumerated_processor_data['id']
    assert serialized == valid_serialization_output(valid_enumerated_processor_data)
