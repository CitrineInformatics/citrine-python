import pytest
from uuid import uuid4
from mock import patch, Mock
from botocore.exceptions import ClientError

from citrine.resources.file_link import FileCollection, FileLink, _Uploader
from tests.utils.session import FakeSession
from tests.utils.factories import FileLinkDataFactory


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> FileCollection:
    return FileCollection(
        project_id=uuid4(),
        dataset_id=uuid4(),
        session=session
    )


@pytest.fixture
def valid_data() -> dict:
    return FileLinkDataFactory(url='www.citrine.io', filename='materials.txt')


def test_build_equivalence(collection, valid_data):
    """Test that build() works the same whether called from FileLink or FileCollection."""
    assert collection.build(valid_data).dump() == FileLink.build(valid_data).dump()


def test_string_representation(valid_data):
    """Test the string representation."""
    assert str(FileLink.build(valid_data)) == '<File link \'materials.txt\'>'


@pytest.fixture
def uploader() -> _Uploader:
    """An _Uploader object with all of its fields filled in."""
    uploader = _Uploader()
    uploader.bucket = 'citrine-datasvc'
    uploader.object_key = '334455'
    uploader.upload_id = 'dea3a-555'
    uploader.region_name = 'us-west'
    uploader.aws_access_key_id = 'sahgkjsgahnei'
    uploader.aws_secret_access_key = 'kdydahkd78452978'
    uploader.aws_session_token = 'sdfhuaf74yf783g4ofg7g3o'
    uploader.object_key = '234787521--abcde'
    uploader.s3_version = '2'
    return uploader


class MockClient(object):
    """A mock version of the S3 client that has a put_object method."""

    def __init__(self, put_object_output):
        self.put_object_output = put_object_output

    def put_object(self, *args, **kwargs):
        """Return the expected output of the real client's put_object method."""
        return self.put_object_output


@patch('citrine.resources.file_link.os.stat')
def test_upload_request(mock_stat, collection, session, uploader):
    """Test that an upload request response contains all required fields."""
    # Mock the method that gets the size of the file.
    mock_stat_object = Mock()
    mock_stat_object.st_size = 17
    mock_stat.return_value = mock_stat_object

    # This is the dictionary structure we expect from the upload request
    upload_request_response = {
        's3_region': uploader.region_name,
        's3_bucket': uploader.bucket,
        'temporary_credentials': {
            'access_key_id': uploader.aws_access_key_id,
            'secret_access_key': uploader.aws_secret_access_key,
            'session_token': uploader.aws_session_token,
        },
        'uploads': [
            {
                's3_key': uploader.object_key,
                'upload_id': uploader.upload_id
            }
        ]
    }
    session.set_response(upload_request_response)
    new_uploader = collection._make_upload_request('foo.txt', 'foo.txt')
    assert new_uploader.bucket == uploader.bucket
    assert new_uploader.object_key == uploader.object_key
    assert new_uploader.upload_id == uploader.upload_id
    assert new_uploader.region_name == uploader.region_name
    assert new_uploader.aws_access_key_id == uploader.aws_access_key_id
    assert new_uploader.aws_secret_access_key == uploader.aws_secret_access_key
    assert new_uploader.aws_session_token == uploader.aws_session_token
    assert new_uploader.object_key == uploader.object_key

    # Using a request response that is missing a field throws a RuntimeError
    del upload_request_response['s3_bucket']
    with pytest.raises(RuntimeError):
        collection._make_upload_request('foo.txt', 'foo.txt')


@patch('citrine.resources.file_link.open')
def test_upload_file(_, collection, uploader):
    """Test that uploading a file returns the version ID."""
    # A successful file upload sets uploader.s3_version
    new_version = '3'
    with patch('citrine.resources.file_link.boto3_client',
               return_value=MockClient({'VersionId': new_version})):
        new_uploader = collection._upload_file('foo.txt', uploader)
        assert new_uploader.s3_version == new_version

    # If the client throws a ClientError when attempting to upload, throw a RuntimeError
    bad_client = Mock()
    bad_client.put_object.side_effect = ClientError(error_response={}, operation_name='put')
    with patch('citrine.resources.file_link.boto3_client',
               return_value=bad_client):
        with pytest.raises(RuntimeError):
            collection._upload_file('foo.txt', uploader)


def test_complete_upload(collection, session, uploader):
    """Test signaling that an upload has completed and the creation of a FileLink object."""
    dest_name = 'foo.txt'
    file_id = '12345'
    version = '13'
    bad_complete_response = {
        'file_info': {
            'file_id': file_id
        },
        'version': version  # 'version' is supposed to go inside 'file_info'
    }
    with pytest.raises(RuntimeError):
        session.set_response(bad_complete_response)
        collection._complete_upload(dest_name, uploader)

    complete_response = {
        'file_info': {
            'file_id': file_id,
            'version': version
        }
    }
    session.set_response(complete_response)
    file_link = collection._complete_upload(dest_name, uploader)
    url = 'projects/{}/datasets/{}/files/{}/versions/{}'\
        .format(collection.project_id, collection.dataset_id, file_id, version)
    assert file_link.dump() == FileLink(dest_name, url=url).dump()
