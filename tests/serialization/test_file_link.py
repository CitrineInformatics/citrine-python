"""Tests of FileLink serialization and deserialization."""
import pytest

from citrine.resources.file_link import FileLink
from tests.utils.factories import FileLinkDataFactory


@pytest.fixture
def valid_data() -> dict:
    return FileLinkDataFactory(url='www.citrine.io', filename='materials.txt')


def test_simple_deserialization(valid_data):
    """Ensure that a deserialized File Link looks sane."""
    file_link = FileLink.build(valid_data)
    assert file_link.url == 'www.citrine.io'
    assert file_link.filename == 'materials.txt'


def test_serialization(valid_data):
    """Ensure that a serialized File Link looks sane."""
    file_link = FileLink.build(valid_data)
    assert file_link.dump() == valid_data
