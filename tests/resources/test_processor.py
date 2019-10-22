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
        'schema_id': '307b88a2-fd50-4d27-ae91-b8d6282f68f7',
    }

    # When
    processor = collection.build(processor_data)

    # Then
    assert processor.uid == processor_id
    assert processor.name == 'My enumerated processor'
    assert processor.max_size == 100
