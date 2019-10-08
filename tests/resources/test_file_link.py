from collections import namedtuple

import pytest
from uuid import uuid4
from mock import patch, Mock
from botocore.exceptions import ClientError

from citrine.resources.file_link import FileCollection, FileLink, _Uploader
from tests.utils.session import FakeSession, FakeS3Client, FakeCall, FakeRequestResponse
from tests.utils.factories import FileLinkDataFactory, _UploaderFactory


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


def test_build_as_dict(collection, valid_data):
    """Test that build() works the same whether called from FileLink or FileCollection."""
    assert collection.build(valid_data).dump() == FileLink.build(valid_data).as_dict()


def test_string_representation(valid_data):
    """Test the string representation."""
    assert str(FileLink.build(valid_data)) == '<File link \'materials.txt\'>'


@pytest.fixture
def uploader() -> _Uploader:
    """An _Uploader object with all of its fields filled in."""
    return _UploaderFactory()


@patch('citrine.resources.file_link.boto3_client')
@patch('citrine.resources.file_link.open')
@patch('citrine.resources.file_link.os.stat')
@patch('citrine.resources.file_link.os.path.isfile')
def test_upload(mock_isfile, mock_stat, mock_open, mock_boto3_client, collection, session):
    """Test signaling that an upload has completed and the creation of a FileLink object."""
    StatStub = namedtuple('StatStub', ['st_size'])

    mock_isfile.return_value = True
    mock_stat.return_value = StatStub(st_size=22300)
    mock_open.return_value.__enter__.return_value = 'Random file contents'
    mock_boto3_client.return_value = FakeS3Client({'VersionId': '3'})

    dest_name = 'foo.txt'
    file_id = '12345'
    version = '13'

    # This is the dictionary structure we expect from the upload completion request
    file_info_response = {
        'file_info': {
            'file_id': file_id,
            'version': version
        }
    }
    uploads_response = {
        's3_region': 'us-east-1',
        's3_bucket': 'temp-bucket',
        'temporary_credentials': {
            'access_key_id': '1234',
            'secret_access_key': 'abbb8777',
            'session_token': 'hefheuhuhhu83772333',
        },
        'uploads': [
            {
                's3_key': '66377378',
                'upload_id': '111',
            }
        ]
    }

    session.set_responses(uploads_response, file_info_response)
    file_link = collection.upload(dest_name)

    assert session.num_calls == 2
    url = 'projects/{}/datasets/{}/files/{}/versions/{}'\
        .format(collection.project_id, collection.dataset_id, file_id, version)
    assert file_link.dump() == FileLink(dest_name, url=url).dump()


def test_upload_missing_file(collection):
    with pytest.raises(ValueError):
        collection.upload('this-file-does-not-exist.xls')


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
    assert session.num_calls == 1
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
               return_value=FakeS3Client({'VersionId': new_version})):
        new_uploader = collection._upload_file('foo.txt', uploader)
        assert new_uploader.s3_version == new_version

    # If the client throws a ClientError when attempting to upload, throw a RuntimeError
    bad_client = Mock()
    bad_client.put_object.side_effect = ClientError(error_response={}, operation_name='put')
    with patch('citrine.resources.file_link.boto3_client',
               return_value=bad_client):
        with pytest.raises(RuntimeError):
            collection._upload_file('foo.txt', uploader)


def test_upload_missing_version(collection, session, uploader):
    dest_name = 'foo.txt'
    file_id = '12345'
    version = '14'

    bad_complete_response = {
        'file_info': {
            'file_id': file_id
        },
        'version': version  # 'version' is supposed to go inside 'file_info'
    }
    with pytest.raises(RuntimeError):
        session.set_response(bad_complete_response)
        collection._complete_upload(dest_name, uploader)


def test_list_file_links(collection, session, valid_data):
    """Test that all files in a dataset can be turned into FileLink and listed."""
    file_id = str(uuid4())
    version = str(uuid4())
    filename = 'materials.txt'
    # The actual response contains more fields, but these are the only ones we use.
    # Crucial thing is that URL ends with "/files/file_id/versions/version"
    returned_data = {
        'filename': filename,
        'versioned_url': "http://citrine.com/api/files/{}/versions/{}".format(file_id, version)
    }
    session.set_response({
        'files': [returned_data]
    })

    files_iterator = collection.list(page=1, per_page=15)
    files = [file for file in files_iterator]

    assert session.num_calls == 1
    expected_call = FakeCall(
        method='GET',
        path=collection._get_path(),
        params={
            'page': 1,
            'per_page': 15
        }
    )
    assert expected_call == session.last_call
    assert len(files) == 1
    expected_url = "projects/{}/datasets/{}/files/{}/versions/{}".format(
        collection.project_id, collection.dataset_id, file_id, version
    )
    expected_file = FileLinkDataFactory(url=expected_url, filename=filename)
    assert files[0].dump() == FileLink.build(expected_file).dump()

    # A response that does not have a URL of the expected form throws ValueError
    bad_returned_data = {
        'filename': filename,
        'versioned_url': "http://citrine.com/api/file_version/{}".format(version)
    }
    session.set_response({
        'files': [bad_returned_data]
    })
    with pytest.raises(ValueError):
        files_iterator = collection.list(page=1, per_page=15)
        [file for file in files_iterator]


@patch('citrine.resources.file_link.open')
@patch('citrine.resources.file_link.requests.get')
@patch('citrine.resources.file_link.os.path.split')
@patch('citrine.resources.file_link.os.path.isdir')
@patch('citrine.resources.file_link.os.makedirs')
def test_file_download(mock_mkdir, mock_os_path_isdir, mock_os_path_split,
                       mock_get, mock_open, collection, session):
    """
    Test that downloading a file works as expected.

    It should make the full file path if only a directory is given, make the directory if
    it does not exist, make a call to get the pre-signed URL, and another to download.
    """
    # Given
    filename = 'diagram.pdf'
    url = "http://citrine.com/api/files/123/versions/456"
    file = FileLink.build(FileLinkDataFactory(url=url, filename=filename))
    pre_signed_url = "http://files.citrine.io/secret-codes/jiifema987pjfsda"  # arbitrary
    session.set_response({
        'pre_signed_read_link': pre_signed_url,
    })
    local_path = 'Users/me/some/new/directory/'

    mock_os_path_split.return_value = (local_path, '')  # triggers appending filename to local_path
    mock_os_path_isdir.return_value = False  # triggers mkdir
    mock_get.return_value = FakeRequestResponse('0101001')  # arbitrary

    # When
    collection.download(file, local_path)

    # When
    assert mock_os_path_isdir.call_count == 1
    assert mock_os_path_split.call_count == 1
    assert mock_mkdir.call_count == 1
    assert mock_get.call_count == 1
    assert mock_open.call_count == 1
    # Mock write should be to path "local_path + filename"
    assert mock_open.mock_calls[0].args[0] == local_path + filename

    expected_call = FakeCall(
        method='GET',
        path=url + '/content-link'
    )
    assert expected_call == session.last_call
