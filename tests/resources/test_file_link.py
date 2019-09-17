import pytest
from uuid import uuid4

from citrine.resources.file_link import FileCollection, FileLink, _Uploader
from tests.utils.session import FakeSession


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
def uploader() -> _Uploader:
    uploader = _Uploader
    uploader.bucket = 'citrine-datasvc'
    uploader.key = '334455'
    uploader.upload_id = 'dea3a-555'
    uploader.region_name = 'us-west'
    uploader.aws_access_key_id = 'sahgkjsgahnei'
    uploader.aws_secret_access_token = 'hjhguneheehhhhsdjfjnjjnelkooius'
    uploader.aws_secret_access_key = 'kdydahkd78452978'
    uploader.aws_session_token = 'sdfhuaf74yf783g4ofg7g3o'
    uploader.object_key = '234787521--abcde'
    uploader.s3_version = '2'
    return uploader


def test_complete_upload(collection, session, uploader):
    """Test the signaling that an upload has completed and the creation of a FileLink object."""
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
