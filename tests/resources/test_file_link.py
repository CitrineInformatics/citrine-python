from collections import namedtuple
from uuid import uuid4

import pytest
import requests_mock
from botocore.exceptions import ClientError
from citrine.resources.file_link import FileCollection, FileLink, _Uploader, \
    FileProcessingType
from mock import patch, Mock, call

from tests.utils.factories import FileLinkDataFactory, _UploaderFactory
from tests.utils.session import FakeSession, FakeS3Client, FakeCall


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


def test_mime_types(collection):
    expected_xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    expected_xls = "application/vnd.ms-excel"
    expected_txt = "text/plain"
    expected_unk = "application/octet-stream"
    expected_csv = "text/csv"

    assert collection._mime_type("asdf.xlsx") == expected_xlsx
    assert collection._mime_type("asdf.XLSX") == expected_xlsx
    assert collection._mime_type("asdf.xls") == expected_xls
    assert collection._mime_type("asdf.TXT") == expected_txt
    assert collection._mime_type("asdf.csv") == expected_csv
    assert collection._mime_type("asdf.FAKE") == expected_unk


def test_build_equivalence(collection, valid_data):
    """Test that build() works the same whether called from FileLink or FileCollection."""
    assert collection.build(valid_data).dump() == FileLink.build(valid_data).dump()


def test_build_as_dict(collection, valid_data):
    """Test that build() works the same whether called from FileLink or FileCollection."""
    assert collection.build(valid_data).dump() == FileLink.build(valid_data).as_dict()


def test_name_alias(valid_data):
    """Test that .name aliases to filename."""
    file = FileLink.build(valid_data)
    assert file.name == file.filename


def test_string_representation(valid_data):
    """Test the string representation."""
    assert str(FileLink.build(valid_data)) == '<File link \'materials.txt\'>'


@pytest.fixture
def uploader() -> _Uploader:
    """An _Uploader object with all of its fields filled in."""
    return _UploaderFactory()


def test_delete(collection, session):
    """Test that deletion calls the expected endpoint and checks the url structure."""
    # Given
    file_id, version_id = str(uuid4()), str(uuid4())
    full_url = 'www.citrine.io/develop/files/{}/versions/{}'.format(file_id, version_id)
    file_link = collection.build(FileLinkDataFactory(url=full_url))

    # When
    collection.delete(file_link)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='DELETE',
        path=collection._get_path(file_id)
    )
    assert expected_call == session.last_call

    # A URL that does not follow the files/{id}/versions/{id} format is invalid
    invalid_url = 'www.citrine.io/develop/filestuff/{}'.format(file_id)
    invalid_file_link = collection.build(FileLinkDataFactory(url=invalid_url))
    with pytest.raises(AssertionError):
        collection.delete(invalid_file_link)


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

    # It would be good to test these, but the values assigned are not accessible
    dest_names = {
        'foo.txt': 'text/plain',
        'foo.TXT': 'text/plain',  # Capitalization in extension is fine
        'foo.bar': 'application/octet-stream'  # No match == generic binary
    }
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

    for dest_name in dest_names:
        session.set_responses(uploads_response, file_info_response)
        file_link = collection.upload(file_path=dest_name)

        url = 'projects/{}/datasets/{}/files/{}/versions/{}'\
            .format(collection.project_id, collection.dataset_id, file_id, version)
        assert file_link.dump() == FileLink(dest_name, url=url).dump()

    assert session.num_calls == 2 * len(dest_names)


def test_upload_missing_file(collection):
    with pytest.raises(ValueError):
        collection.upload(file_path='this-file-does-not-exist.xls')


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
    assert new_uploader.s3_endpoint_url == uploader.s3_endpoint_url
    assert new_uploader.s3_use_ssl == uploader.s3_use_ssl
    assert new_uploader.s3_addressing_style == uploader.s3_addressing_style

    # Using a request response that is missing a field throws a RuntimeError
    del upload_request_response['s3_bucket']
    with pytest.raises(RuntimeError):
        collection._make_upload_request('foo.txt', 'foo.txt')


@patch('citrine.resources.file_link.os.stat')
def test_upload_request_s3_overrides(mock_stat, collection, session, uploader):
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

    # Override the s3 endpoint settings in the session, ensure they make it to the upload
    endpoint = 'http://foo.bar'
    addressing_style = 'path'
    use_ssl = False
    session.s3_endpoint_url = endpoint
    session.s3_addressing_style = addressing_style
    session.s3_use_ssl = use_ssl

    new_uploader = collection._make_upload_request('foo.txt', 'foo.txt')
    assert new_uploader.s3_endpoint_url == endpoint
    assert new_uploader.s3_use_ssl == use_ssl
    assert new_uploader.s3_addressing_style == addressing_style


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

    s3_addressing_style = 'path'
    s3_endpoint_url = 'http://foo.bar'
    s3_use_ssl = False

    uploader.s3_addressing_style = s3_addressing_style
    uploader.s3_endpoint_url = s3_endpoint_url
    uploader.s3_use_ssl = s3_use_ssl

    s3_override_client = Mock()
    s3_override_client.put_object.return_value = {'VersionId': '3'}

    with patch('citrine.resources.file_link.boto3_client',
               return_value=s3_override_client) as mock_boto_client:
        collection._upload_file('foo.txt', uploader)

        # Ensure we're connecting to S3 with the proper parameter overrides for a different endpoint.
        assert mock_boto_client.call_args.kwargs['config'].s3['addressing_style'] is s3_addressing_style
        assert mock_boto_client.call_args.kwargs['endpoint_url'] is s3_endpoint_url
        assert mock_boto_client.call_args.kwargs['use_ssl'] is s3_use_ssl


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

    files_iterator = collection.list(per_page=15)
    files = [file for file in files_iterator]

    assert session.num_calls == 1
    expected_call = FakeCall(
        method='GET',
        path=collection._get_path(),
        params={
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
    with pytest.warns(DeprecationWarning):
        with pytest.raises(ValueError):
            files_iterator = collection.list(page=1, per_page=15)
            [file for file in files_iterator]


@patch("citrine.resources.file_link.write_file_locally")
def test_file_download(mock_write_file_locally, collection, session):
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

    with requests_mock.mock() as mock_get:
        mock_get.get(pre_signed_url, text='0101001')

        # When
        collection.download(file_link=file, local_path=local_path)

        # When
        assert mock_get.call_count == 1
        expected_call = FakeCall(
            method='GET',
            path=url + '/content-link'
        )
        assert expected_call == session.last_call
        assert mock_write_file_locally.call_count == 1
        assert mock_write_file_locally.call_args == call(b'0101001', local_path + file.filename)


def test_process_file(collection, session):
    """Test processing an existing file."""

    file_id, version_id = str(uuid4()), str(uuid4())
    full_url = 'www.citrine.io/develop/files/{}/versions/{}'.format(file_id, version_id)
    file_link = collection.build(FileLinkDataFactory(url=full_url))

    job_id_resp = {
        'job_id': str(uuid4())
    }
    job_execution_resp = {
        'status': 'Success',
        'job_type': 'something',
        'tasks': []
    }
    file_processing_result_resp = {
        'results': [
            {
                'processing_type': 'VALIDATE_CSV',
                'data': {
                    'columns': [
                        {
                            'name': 'a',
                            'bounds': {
                                'type': 'integer_bounds',
                                'lower_bound': 0,
                                'upper_bound': 10
                            },
                            'exact_range_bounds': {
                                'type': 'integer_bounds',
                                'lower_bound': 0,
                                'upper_bound': 10
                            }
                        }
                    ],
                    'record_count': 123
                }
            }
        ]
    }

    # First does a PUT on the /processed endpoint
    # then does a GET on the job executions endpoint
    # then gets the file processing result
    session.set_responses(job_id_resp, job_execution_resp, file_processing_result_resp)
    collection.process(file_link=file_link, processing_type=FileProcessingType.VALIDATE_CSV)

def test_process_file_no_waiting(collection, session):
    """Test processing an existing file without waiting on the result."""

    file_id, version_id = str(uuid4()), str(uuid4())
    full_url = 'www.citrine.io/develop/files/{}/versions/{}'.format(file_id, version_id)
    file_link = collection.build(FileLinkDataFactory(url=full_url))

    job_id_resp = {
        'job_id': str(uuid4())
    }

    # First does a PUT on the /processed endpoint
    # then does a GET on the job executions endpoint
    session.set_response(job_id_resp)
    resp = collection.process(file_link=file_link, processing_type=FileProcessingType.VALIDATE_CSV,
                              wait_for_response=False)
    assert str(resp.job_id) == job_id_resp['job_id']