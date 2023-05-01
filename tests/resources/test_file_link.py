from boto3 import Session
from botocore.exceptions import ClientError
from pathlib import Path
import pytest
from uuid import uuid4, UUID

import requests_mock

from citrine.resources.api_error import ValidationError
from citrine.resources.file_link import FileCollection, FileLink, _Uploader, \
    FileProcessingType
from citrine.exceptions import NotFound

from tests.utils.factories import FileLinkDataFactory, _UploaderFactory
from tests.utils.session import FakeSession, FakeS3Client, FakeCall, FakeRequestResponseApiError


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


def test_mime_types(collection: FileCollection):
    expected_xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    expected_xls = "application/vnd.ms-excel"
    expected_txt = "text/plain"
    expected_unk = "application/octet-stream"
    expected_csv = "text/csv"

    assert collection._mime_type(Path("asdf.xlsx")) == expected_xlsx
    assert collection._mime_type(Path("asdf.XLSX")) == expected_xlsx
    assert collection._mime_type(Path("asdf.xls")) == expected_xls
    assert collection._mime_type(Path("asdf.TXT")) == expected_txt
    assert collection._mime_type(Path("asdf.csv")) == expected_csv
    assert collection._mime_type(Path("asdf.FAKE")) == expected_unk


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


def test_delete(collection: FileCollection, session):
    """Test that deletion calls the expected endpoint and checks the url structure."""
    # Given
    file_id, version_id = str(uuid4()), str(uuid4())
    full_url = collection._get_path(uid=file_id, version=version_id)
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
    for chunk in (f'{file_id}', f'{file_id}/{version_id}'):
        invalid_url = f'{collection._get_path}/{chunk}'
        invalid_file_link = collection.build(FileLinkDataFactory(url=invalid_url))
        with pytest.raises(ValueError):
            collection.delete(invalid_file_link)

    # A remote URL is invalid
    ext_invalid_url = f'http://www.citrine.io/develop/files/{file_id}/versions/{version_id}'
    ext_invalid_file_link = collection.build(FileLinkDataFactory(url=ext_invalid_url))
    with pytest.raises(ValueError):
        collection.delete(ext_invalid_file_link)


def test_upload(collection: FileCollection, session, tmpdir, monkeypatch):
    """Test signaling that an upload has completed and the creation of a FileLink object."""
    monkeypatch.setattr(Session, 'client', lambda *args, **kwargs: FakeS3Client({'VersionId': '42'}))
    # It would be good to test these, but the values assigned are not accessible
    dest_names = {
        'foo.txt': 'text/plain',
        'foo.TXT': 'text/plain',  # Capitalization in extension is fine
        'foo.bar': 'application/octet-stream'  # No match == generic binary
    }
    file_id = str(uuid4())
    version = str(uuid4())

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
        tmp_path = Path(tmpdir) / dest_name
        tmp_path.write_text("Something")

        session.set_responses(uploads_response, file_info_response)
        file_link = collection.upload(file_path=tmp_path)

        url = 'projects/{}/datasets/{}/files/{}/versions/{}'\
            .format(collection.project_id, collection.dataset_id, file_id, version)
        assert file_link.dump() == FileLink(dest_name, url=url).dump()

    assert session.num_calls == 2 * len(dest_names)


def test_upload_missing_file(collection: FileCollection):
    with pytest.raises(ValueError):
        collection.upload(file_path='this-file-does-not-exist.xls')


def test_upload_request(collection: FileCollection, session, uploader, tmpdir):
    """Test that an upload request response contains all required fields."""
    filename = 'foo.txt'
    tmppath = Path(tmpdir) / filename
    tmppath.write_text("Arbitrary text")

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
    new_uploader = collection._make_upload_request(tmppath, filename)
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
        collection._make_upload_request(tmppath, filename)


def test_upload_request_s3_overrides(collection: FileCollection, session, uploader, tmpdir):
    """Test that an upload request response contains all required fields."""
    filename = 'foo.txt'
    tmppath = Path(tmpdir) / filename
    tmppath.write_text("Arbitrary text")

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

    new_uploader = collection._make_upload_request(tmppath, filename)
    assert new_uploader.s3_endpoint_url == endpoint
    assert new_uploader.s3_use_ssl == use_ssl
    assert new_uploader.s3_addressing_style == addressing_style


def test_upload_file(collection: FileCollection, session, uploader, tmpdir, monkeypatch):
    """Test that uploading a file returns the version ID."""
    filename = 'foo.txt'
    tmppath = Path(tmpdir) / filename
    tmppath.write_text("Arbitrary text")

    # A successful file upload sets uploader.s3_version
    new_version = '3'
    with monkeypatch.context() as m:
        client = FakeS3Client({'VersionId': new_version})
        m.setattr(Session, 'client', lambda *args, **kwargs: client)
        new_uploader = collection._upload_file(tmppath, uploader)
        assert new_uploader.s3_version == new_version

    # If the client throws a ClientError when attempting to upload, throw a RuntimeError
    with monkeypatch.context() as m:
        client = FakeS3Client(ClientError(error_response={}, operation_name='put'), raises=True)
        m.setattr(Session, 'client', lambda *args, **kwargs: client)

        with pytest.raises(RuntimeError):
            collection._upload_file(tmppath, uploader)

    s3_addressing_style = 'path'
    s3_endpoint_url = 'http://foo.bar'
    s3_use_ssl = False

    uploader.s3_addressing_style = s3_addressing_style
    uploader.s3_endpoint_url = s3_endpoint_url
    uploader.s3_use_ssl = s3_use_ssl

    with monkeypatch.context() as m:
        stashed_kwargs = {}

        def _stash_kwargs(*_, **kwargs):
            stashed_kwargs.update(kwargs)
            return FakeS3Client({'VersionId': '71'})

        m.setattr(Session, 'client', _stash_kwargs)
        collection._upload_file(tmppath, uploader)

        assert stashed_kwargs['config'].s3['addressing_style'] is s3_addressing_style
        assert stashed_kwargs['endpoint_url'] is s3_endpoint_url
        assert stashed_kwargs['use_ssl'] is s3_use_ssl


def test_upload_missing_version(collection: FileCollection, session, uploader):
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


def test_list_file_links(collection: FileCollection, session, valid_data):
    """Test that all files in a dataset can be turned into FileLink and listed."""
    file_id = str(uuid4())
    version = str(uuid4())
    filename = 'materials.txt'
    # The actual response contains more fields, but these are the only ones we use.
    returned_data = {
        'id': file_id,
        'version': version,
        'filename': filename,
    }
    returned_data["unversioned_url"] = f"http://test.domain.net:8002/api/v1/files/{returned_data['id']}"
    returned_data["versioned_url"] = f"http://test.domain.net:8002/api/v1/files/{returned_data['id']}" \
                                     f"/versions/{returned_data['version']}"
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
            'per_page': 15,
            'page': 1
        }
    )
    assert expected_call == session.last_call
    assert len(files) == 1
    expected_url = "projects/{}/datasets/{}/files/{}/versions/{}".format(
        collection.project_id, collection.dataset_id, file_id, version
    )
    expected_file = FileLinkDataFactory(url=expected_url, filename=filename)
    assert files[0].dump() == FileLink.build(expected_file).dump()


def test_file_download(collection: FileCollection, session, tmpdir):
    """
    Test that downloading a file works as expected.

    It should make the full file path if only a directory is given, make the directory if
    it does not exist, make a call to get the pre-signed URL, and another to download.
    """
    # Given
    filename = 'diagram.pdf'
    file_uid = str(uuid4())
    version_uid = str(uuid4())
    url = f"projects/{collection.project_id}/datasets/{collection.dataset_id}/files/{file_uid}/versions/{version_uid}"
    file = FileLink.build(FileLinkDataFactory(url=url, filename=filename, id=file_uid, version=version_uid))
    pre_signed_url = "http://files.citrine.io/secret-codes/jiifema987pjfsda"  # arbitrary
    session.set_response({
        'pre_signed_read_link': pre_signed_url,
    })
    target_dir = str(tmpdir) + 'some/new/directory/'
    target_file = target_dir + filename

    def _checked_write(path, content):
        with requests_mock.mock() as mock_get:
            mock_get.get(pre_signed_url, text=content)
            # When
            collection.download(file_link=file, local_path=path)

            # When
            assert mock_get.call_count == 1
            expected_call = FakeCall(
                method='GET',
                path=url + '/content-link'
            )
            assert expected_call == session.last_call

    _checked_write(target_dir, 'content')
    assert Path(target_file).read_text() == 'content'

    # Now the directory exists
    _checked_write(Path(target_dir), 'other content')
    assert Path(target_file).read_text() == 'other content'

    # Give it the filename instead
    _checked_write(target_file, 'more content')
    assert Path(target_file).read_text() == 'more content'

    # And as a Path
    _checked_write(target_file, 'love that content')
    assert Path(target_file).read_text() == 'love that content'

    bad_url = f"bin/uuid3/versions/uuid4"
    bad_file = FileLink.build(FileLinkDataFactory(url=bad_url, filename=filename))
    with pytest.raises(ValueError, match="malformed"):
        collection.download(file_link=bad_file, local_path=target_dir)


def test_read(collection: FileCollection, session):
    """
    Test that reading a file works as expected.

    """
    # Given
    filename = 'diagram.pdf'
    file_uid = str(uuid4())
    version_uid = str(uuid4())
    url = f"projects/{collection.project_id}/datasets/{collection.dataset_id}/files/{file_uid}/versions/{version_uid}"
    file = FileLink.build(FileLinkDataFactory(url=url, filename=filename, id=file_uid, version=version_uid))
    pre_signed_url = "http://files.citrine.io/secret-codes/jiifema987pjfsda"  # arbitrary
    session.set_response({
        'pre_signed_read_link': pre_signed_url,
    })
   
    with requests_mock.mock() as mock_get:
        mock_get.get(pre_signed_url, text="lorem ipsum")
        # When
        io = collection.read(file_link=file)
        assert io.decode('UTF-8') == 'lorem ipsum'
        # When
        assert mock_get.call_count == 1
        expected_call = FakeCall(
            method='GET',
            path=url + '/content-link'
        )
        assert expected_call == session.last_call

    bad_url = f"bin/uuid3/versions/uuid4"
    bad_file = FileLink.build(FileLinkDataFactory(url=bad_url, filename=filename))
    with pytest.raises(ValueError, match="malformed"):
        collection.read(file_link=bad_file)

    # Test with files.list endpoint-like object
    filelink = collection.build({"id": str(uuid4()),
                                 "version": str(uuid4()),
                                 "filename": filename,
                                 "type": FileLink.typ})
    pre_signed_url_2 = "http://files.citrine.io/secret-codes/2222222222222"  # arbitrary
    session.set_response({'pre_signed_read_link': pre_signed_url_2})
    with requests_mock.mock() as mock_get:
        mock_get.get(pre_signed_url_2, text="quite lovely")
        # When
        io = collection.read(file_link=filelink)
        assert io.decode('UTF-8') == 'quite lovely'
        # When
        assert mock_get.call_count == 1
        expected_call_2 = FakeCall(
            method='GET',
            path=filelink.url + '/content-link'
        )
        assert expected_call_2 == session.last_call


def test_external_file_read(collection: FileCollection, session):
    """
    Test that reading a file works as expected for external files.

    """
    # Given
    filename = 'spreadsheet.xlsx'
    url = "http://customer.com/data-lake/files/123/versions/456"
    file = FileLink.build(FileLinkDataFactory(url=url, filename=filename))

    with requests_mock.mock() as mock_get:
        mock_get.get(url, text='010111011')

        # When
        io = collection.read(file_link=file)
        assert io.decode('UTF-8') == '010111011'

        # When
        assert mock_get.call_count == 1


def test_external_file_download(collection: FileCollection, session, tmpdir):
    """
    Test that downloading a file works as expected for external files.

    It should make the full file path if only a directory is given, make the directory if
    it does not exist, and make a single call to download.
    """
    # Given
    filename = 'spreadsheet.xlsx'
    url = "http://customer.com/data-lake/files/123/versions/456"
    file = FileLink.build(FileLinkDataFactory(url=url, filename=filename))
    local_path = Path(tmpdir) / 'test_external_file_download/new_name.xlsx'

    with requests_mock.mock() as mock_get:
        mock_get.get(url, text='010111011')

        # When
        collection.download(file_link=file, local_path=local_path)

        # When
        assert mock_get.call_count == 1

    assert local_path.read_text() == '010111011'


def test_process_file(collection: FileCollection, session):
    """Test processing an existing file."""

    file_id, version_id = str(uuid4()), str(uuid4())
    full_url = collection._get_path(uid=file_id, version=version_id)
    file_link = collection.build(FileLinkDataFactory(url=full_url, id=file_id, version=version_id))

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
    with pytest.warns(DeprecationWarning):
        collection.process(file_link=file_link, processing_type=FileProcessingType.VALIDATE_CSV)


def test_process_file_no_waiting(collection: FileCollection, session):
    """Test processing an existing file without waiting on the result."""

    file_id, version_id = str(uuid4()), str(uuid4())
    full_url = collection._get_path(uid=file_id, version=version_id)
    file_link = collection.build(FileLinkDataFactory(url=full_url, id=file_id, version=version_id))

    job_id_resp = {
        'job_id': str(uuid4())
    }

    # First does a PUT on the /processed endpoint
    # then does a GET on the job executions endpoint
    session.set_response(job_id_resp)
    with pytest.warns(DeprecationWarning):
        resp = collection.process(file_link=file_link, processing_type=FileProcessingType.VALIDATE_CSV,
                                  wait_for_response=False)
    assert str(resp.job_id) == job_id_resp['job_id']


def test_process_file_exceptions(collection: FileCollection, session):
    """Test processing an existing file without waiting on the result."""
    full_url = f'http://www.files.com/file.path'
    file_link = collection.build(FileLinkDataFactory(url=full_url))
    collection._get_path()
    # First does a PUT on the /processed endpoint
    # then does a GET on the job executions endpoint
    with pytest.raises(ValueError, match="on-platform resources"):
        with pytest.warns(DeprecationWarning):
            collection.process(file_link=file_link,
                               processing_type=FileProcessingType.VALIDATE_CSV,
                               wait_for_response=False)


def test_ingest(collection: FileCollection, session):
    """Test the on-platform ingest route."""
    good_file1 = collection.build({"filename": "good.csv", "id": str(uuid4()), "version": str(uuid4())})
    good_file2 = collection.build({"filename": "also.csv", "id": str(uuid4()), "version": str(uuid4())})
    bad_file = FileLink(filename="bad.csv", url="http://files.com/input.csv")

    job_id_resp = {
        'ingestion_id': str(uuid4())
    }
    session.set_responses(job_id_resp, job_id_resp)
    collection.ingest([good_file1, good_file2])

    with pytest.raises(ValueError, match=bad_file.url):
        collection.ingest([good_file1, bad_file])


def test_resolve_file_link(collection: FileCollection, session):
    # The actual response contains more fields, but these are the only ones we use.
    raw_files = [
        {
            'id': str(uuid4()),
            'version': str(uuid4()),
            'filename': 'file0.txt',
            'version_number': 1
        },
        {
            'id': str(uuid4()),
            'version': str(uuid4()),
            'filename': 'file1.txt',
            'version_number': 3
        },
        {
            'id': str(uuid4()),
            'version': str(uuid4()),
            'filename': 'file2.txt',
            'version_number': 1
        },
    ]
    file1_versions = [raw_files[1].copy() for _ in range(3)]
    file1_versions[0]['version'] = str(uuid4())
    file1_versions[0]['version_number'] = 1
    file1_versions[2]['version'] = str(uuid4())
    file1_versions[2]['version_number'] = 2
    for raw in raw_files:
        raw['unversioned_url'] = f"http://test.domain.net:8002/api/v1/files/{raw['id']}"
        raw['versioned_url'] = f"http://test.domain.net:8002/api/v1/files/{raw['id']}/versions/{raw['version']}"
    for f1 in file1_versions:
        f1['unversioned_url'] = f"http://test.domain.net:8002/api/v1/files/{f1['id']}"
        f1['versioned_url'] = f"http://test.domain.net:8002/api/v1/files/{f1['id']}/versions/{f1['version']}"

    session.set_response({
        'files': raw_files
    })

    file1 = collection.build(raw_files[1])

    assert collection._resolve_file_link(file1) == file1, "Resolving a FileLink is a no-op"
    assert session.num_calls == 0, "No-op still hit server"

    session.set_response({
        'files': [raw_files[1]]
    })

    unresolved = FileLink(filename=file1.filename, url=file1.url)
    assert collection._resolve_file_link(unresolved) == file1, "FileLink didn't resolve"
    assert session.num_calls == 1

    unresolved.filename = "Wrong.file"
    with pytest.raises(ValueError):
        collection._resolve_file_link(unresolved)
    assert session.num_calls == 2

    assert collection._resolve_file_link(UUID(raw_files[1]['id'])) == file1, "UUID didn't resolve"
    assert session.num_calls == 3

    session.set_response({
        'files': [raw_files[1]]
    })
    assert collection._resolve_file_link(raw_files[1]['id']) == file1, "String UUID didn't resolve"
    assert session.num_calls == 4

    assert collection._resolve_file_link(raw_files[1]['version']) == file1, "Version UUID didn't resolve"
    assert session.num_calls == 5

    abs_link = "https://wwww.website.web/web.pdf"
    assert collection._resolve_file_link(abs_link).filename == "web.pdf"
    assert collection._resolve_file_link(abs_link).url == abs_link

    session.set_response({
        'files': [raw_files[1]]
    })
    assert collection._resolve_file_link(file1.url) == file1, "Relative path didn't resolve"
    assert session.num_calls == 6

    session.set_response({
        'files': [raw_files[1]]
    })
    assert collection._resolve_file_link(file1.filename) == file1, "Filename didn't resolve"
    assert session.num_calls == 7

    with pytest.raises(TypeError):
        collection._resolve_file_link(12345)
    assert session.num_calls == 7


def test_get_ids_from_url(collection: FileCollection):
    good = [
        f"projects/{uuid4()}/datasets/{uuid4()}/files/{uuid4()}/versions/{uuid4()}",
        f"/files/{uuid4()}/versions/{uuid4()}",
    ]
    file = [
        f"projects/{uuid4()}/datasets/{uuid4()}/files/{uuid4()}",
        f"/files/{uuid4()}",
    ]
    bad = [
        f"/projects/{uuid4()}/datasets/{uuid4()}/files/{uuid4()}/versions/{uuid4()}/action",
        f"/projects/{uuid4()}/datasets/{uuid4()}/{uuid4()}/versions/{uuid4()}",
        f"projects/{uuid4()}/datasets/{uuid4()}/files/{uuid4()}/versions/{uuid4()}?query=param",
        f"projects/{uuid4()}/datasets/{uuid4()}/files/{uuid4()}/versions/{uuid4()}?#fragment",
        "http://customer.com/data-lake/files/123/versions/456",
        "/files/uuid4/versions/uuid4",
    ]
    for x in good:
        assert collection._get_ids_from_url(x)[0] is not None
        assert collection._get_ids_from_url(x)[1] is not None
    for x in file:
        assert collection._get_ids_from_url(x)[0] is not None
        assert collection._get_ids_from_url(x)[1] is None
    for x in bad:
        assert collection._get_ids_from_url(x)[0] is None
        assert collection._get_ids_from_url(x)[1] is None


def test_get(collection: FileCollection, session):
    raw_files = [
        {
            'id': str(uuid4()),
            'version': str(uuid4()),
            'filename': 'file0.txt',
            'version_number': 1
        },
        {
            'id': str(uuid4()),
            'version': str(uuid4()),
            'filename': 'file1.txt',
            'version_number': 3
        },
        {
            'id': str(uuid4()),
            'version': str(uuid4()),
            'filename': 'file2.txt',
            'version_number': 1
        },
    ]
    file1_versions = [raw_files[1].copy() for _ in range(3)]
    file1_versions[0]['version'] = str(uuid4())
    file1_versions[0]['version_number'] = 1
    file1_versions[2]['version'] = str(uuid4())
    file1_versions[2]['version_number'] = 2
    for raw in raw_files:
        raw['unversioned_url'] = f"http://test.domain.net:8002/api/v1/files/{raw['id']}"
        raw['versioned_url'] = f"http://test.domain.net:8002/api/v1/files/{raw['id']}/versions/{raw['version']}"
    for f1 in file1_versions:
        f1['unversioned_url'] = f"http://test.domain.net:8002/api/v1/files/{f1['id']}"
        f1['versioned_url'] = f"http://test.domain.net:8002/api/v1/files/{f1['id']}/versions/{f1['version']}"
    file0 = collection.build(raw_files[0])
    file1 = collection.build(raw_files[1])

    session.set_response({
        'files': [raw_files[1]]
    })
    assert collection.get(uid=raw_files[1]['id'], version=raw_files[1]['version']) == file1

    session.set_response({
        'files': [raw_files[0]]
    })
    assert collection.get(uid=raw_files[0]['id'], version=raw_files[0]['version_number']) == file0

    session.set_response({
        'files': [raw_files[1]]
    })
    assert collection.get(uid=raw_files[1]['filename'], version=raw_files[1]['version_number']) == file1

    session.set_response({
        'files': [raw_files[1]]
    })
    assert collection.get(uid=raw_files[1]['filename'], version=raw_files[1]['version']) == file1

    validation_error = ValidationError.build({"failure_message": "file not found", "failure_id": "failure_id"})
    session.set_response(
        NotFound("path", FakeRequestResponseApiError(400, "Not found", [validation_error]))
    )
    with pytest.raises(NotFound):
        collection.get(uid=raw_files[1]['filename'], version=4)


def test_exceptions(collection: FileCollection, session):
    file_link = FileLink(url="http://customer.com/data-lake/files/123/versions/456", filename="456")
    with pytest.raises(ValueError):
        collection._get_path_from_file_link(file_link)

    with pytest.raises(TypeError):
        collection.get(uid=12345)

    with pytest.raises(TypeError):
        collection.get(uid=uuid4(), version=set())

    with pytest.raises(ValueError):
        collection.get(uid=uuid4(), version="Words!")

    validation_error = ValidationError.build({"failure_message": "file not found", "failure_id": "failure_id"})
    session.set_response(
        NotFound("path", FakeRequestResponseApiError(400, "Not found", [validation_error]))
    )
    with pytest.raises(NotFound):
        collection.get(uid="name")
