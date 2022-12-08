import uuid
from copy import deepcopy

import pytest

from citrine.resources.processor import ProcessorCollection


@pytest.fixture
def processor_data():
    return {
        'id': str(uuid.uuid4()),
        'config': {
            'type': 'Enumerated',
            'name': 'My enumerated processor',
            'description': 'For testing',
            'max_size': 100,
        },
        'status': '',
    }


def test_processor_build(processor_data):
    # Given
    collection = ProcessorCollection(uuid.uuid4(), None)
    processor_id = processor_data["id"]

    # When
    processor = collection.build(processor_data)

    # Then
    assert str(processor.uid) == processor_id
    assert processor.name == 'My enumerated processor'
    assert processor.max_candidates == 100


def test_processor_build_with_status(processor_data):
    # Given
    status_detail_data = {("Info", "info_msg"), ("Warning", "warning msg"), ("Error", "error msg")}
    data = deepcopy(processor_data)
    data["status_detail"] = [{"level": level, "msg": msg} for level, msg in status_detail_data]

    # When
    collection = ProcessorCollection(uuid.uuid4(), None)
    processor = collection.build(data)

    # Then
    status_detail_tuples = {(detail.level, detail.msg) for detail in processor.status_detail}
    assert status_detail_tuples == status_detail_data
