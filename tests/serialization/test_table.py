from uuid import uuid4, UUID

import pytest
from random import randrange

from citrine.resources.table import Table


@pytest.fixture
def valid_data():
    """Return valid data used for these tests"""
    return dict(
        id=str(uuid4()),
        version=randrange(10),
        signed_download_url="https://s3.amazonaws.citrine.io/bucketboi"
    )


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized Table looks normal."""
    table: Table = Table.build(valid_data)
    assert table.uid == UUID(valid_data['id'])
    assert table.version == valid_data["version"]
    assert table.download_url == "https://s3.amazonaws.citrine.io/bucketboi"


def test_simple_serialization(valid_data):
    table: Table = Table.build(valid_data)
    serialized = table.dump()
    assert serialized == valid_data
