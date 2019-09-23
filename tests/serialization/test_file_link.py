"""Tests of FileLink serialization and deserialization."""
from citrine.resources.file_link import FileLink
from tests.utils.factories import FileLinkDataFactory


def test_simple_deserialization():
    """Ensure that a deserialized File Link looks sane."""
    valid_data = FileLinkDataFactory(url='www.citrine.io', filename='materials.txt')
    file_link = FileLink.build(valid_data)
    assert file_link.url == 'www.citrine.io'
    assert file_link.filename == 'materials.txt'


def test_serialization():
    """Ensure that a serialized File Link looks sane."""
    valid_data = FileLinkDataFactory(url='www.citrine.io', filename='materials.txt')
    file_link = FileLink.build(valid_data)
    assert file_link.dump() == valid_data
