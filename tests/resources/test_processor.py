import uuid

from citrine.resources.processor import ProcessorCollection


def test_processor_build():
    # Given
    collection = ProcessorCollection(uuid.uuid4(), None)
    processor_id = uuid.uuid4()
    processor_data = {
        'id': str(processor_id),
        'config': {
            'type': 'Enumerated',
            'name': 'My enumerated processor',
            'description': 'For testing',
            'max_size': 100,
        },
        'status': '',
    }

    # When
    processor = collection.build(processor_data)

    # Then
    assert processor.uid == processor_id
    assert processor.name == 'My enumerated processor'
    assert processor.max_candidates == 100
