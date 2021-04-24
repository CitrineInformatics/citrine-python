import uuid
import mock
import pytest

from citrine.exceptions import NotFound
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
    assert processor.max_size == 100


def test_delete():
    pc = ProcessorCollection(uuid.uuid4(), mock.Mock())
    with pytest.raises(NotImplementedError):
        pc.delete(uuid.uuid4())


def test_archive(valid_grid_processor_data):
    session = mock.Mock()
    pc = ProcessorCollection(uuid.uuid4(), session)
    session.get_resource.return_value = valid_grid_processor_data

    def _mock_put_resource(url, data):
        """Assume that update returns the serialized processor data."""
        return data
    session.put_resource.side_effect = _mock_put_resource
    archived_processor = pc.archive(uuid.uuid4())
    assert archived_processor.archived

    session.get_resource.side_effect = NotFound("")
    with pytest.raises(RuntimeError):
        pc.archive(uuid.uuid4())
