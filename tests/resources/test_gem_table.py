import json
from uuid import UUID, uuid4

import pytest
import requests_mock
from mock import patch, call

from citrine.exceptions import JobFailureError, PollingTimeoutError
from citrine.resources.table_config import TableConfig
from citrine.resources.gemtables import GemTableCollection, GemTable
from tests.utils.factories import GemTableDataFactory, ListGemTableVersionsDataFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> GemTableCollection:
    return GemTableCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        session=session
    )


@pytest.fixture
def table():
    def _table(download_url: str) -> GemTable:
        return GemTable.build(GemTableDataFactory(signed_download_url=download_url, version=2))

    return _table


def test_get_table_metadata(collection, session):
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    gem_table = GemTableDataFactory()
    session.set_response(gem_table)

    # When
    retrieved_table: GemTable = collection.get(gem_table["id"], version=gem_table["version"])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="GET",
        path="projects/{}/display-tables/{}/versions/{}".format(project_id, gem_table["id"], gem_table["version"])
    )
    assert session.last_call == expect_call
    assert str(retrieved_table.uid) == gem_table["id"]
    assert retrieved_table.version == gem_table["version"]
    assert retrieved_table.download_url == gem_table["signed_download_url"]

    # Given
    gem_tables = ListGemTableVersionsDataFactory()
    session.set_response(gem_tables)
    version_number = max([table["version"] for table in gem_tables["tables"]])

    # When
    retrieved_table = collection.get(gem_table["id"])

    # Then
    assert retrieved_table.version == version_number


def test_list_tables(collection, session):
    # Given
    table_versions = ListGemTableVersionsDataFactory()
    session.set_response(table_versions)

    # When
    results = list(collection.list())

    # Then
    assert len(results) == 3
    assert results[0].uid is not None


def test_list_table_versions(collection, session):
    # Given
    table_versions = ListGemTableVersionsDataFactory()
    session.set_response(table_versions)

    # When
    results = list(collection.list_versions(table_versions['tables'][0]['id']))

    # Then
    assert len(results) == 3
    assert results[0].uid is not None


def test_list_by_config(collection, session):
    # Given
    table_versions = ListGemTableVersionsDataFactory()
    session.set_response(table_versions)

    # When
    # NOTE: list_by_config returns slightly more info in this call, but it's a superset of
    # a typical Table, and parsed identically in citrine-python.
    results = list(collection.list_by_config(table_versions['tables'][0]['id']))

    # Then
    assert len(results) == 3
    assert results[0].uid is not None


def test_init_table():
    gem_table = GemTable()
    assert gem_table.uid is None
    assert gem_table.version is None
    assert gem_table.download_url is None


def test_str_serialization(table):
    t = table("http://somewhere.cool")
    assert str(t) == "<GEM Table {!r}, version {}>".format(t.uid, 2)


def test_register_table(collection):
    with pytest.raises(RuntimeError):
        collection.register(GemTable.build(GemTableDataFactory()))


def test_update_table(collection, table):
    with pytest.raises(RuntimeError):
        collection.update(GemTable.build(GemTableDataFactory()))


def test_delete_table(collection, table):
    with pytest.raises(NotImplementedError):
        collection.delete(GemTable.build(GemTableDataFactory()).uid)


def test_build_from_config(collection: GemTableCollection, session):
    config_uid = uuid4()
    config_version = 2
    config = TableConfig(
        name='foo',
        description='bar',
        columns=[],
        rows=[],
        variables=[],
        datasets=[]
    )
    config.config_uid = config_uid
    config.version_number = config_version
    expected_table_data = GemTableDataFactory()
    session.set_responses(
        {'job_id': '12345678-1234-1234-1234-123456789ccc'},
        {'job_type': 'foo', 'status': 'In Progress', 'tasks': []},
        {'job_type': 'foo', 'status': 'Success', 'tasks': [], 'output': {
            'display_table_id': expected_table_data['id'],
            'display_table_version': str(expected_table_data['version']),
            'table_warnings': json.dumps([
                {'limited_results': ['foo', 'bar'], 'total_count': 3},
            ])
        }},
        expected_table_data,
    )
    gem_table = collection.build_from_config(config, version='ignored')
    assert isinstance(gem_table, GemTable)
    assert session.num_calls == 4


def test_build_from_config_failures(collection: GemTableCollection, session):
    with pytest.raises(ValueError):
        collection.build_from_config(uuid4())
    config = TableConfig(
        name='foo',
        description='bar',
        columns=[],
        rows=[],
        variables=[],
        datasets=[]
    )
    config.definition_uid = uuid4()
    with pytest.raises(ValueError):
        collection.build_from_config(config)
    config.version_number = 1
    config.config_uid = None
    with pytest.raises(ValueError):
        collection.build_from_config(config)
    config.config_uid = uuid4()
    session.set_responses(
        {'job_id': '12345678-1234-1234-1234-123456789ccc'},
        {'job_type': 'foo', 'status': 'Failure', 'tasks': [
            {'task_type': 'foo', 'id': 'foo', 'status': 'Failure', 'failure_reason': 'because', 'dependencies': []}
        ]},
    )
    with pytest.raises(JobFailureError):
        collection.build_from_config(uuid4(), version=1)
    session.set_responses(
        {'job_id': '12345678-1234-1234-1234-123456789ccc'},
        {'job_type': 'foo', 'status': 'In Progress', 'tasks': []},
    )
    with pytest.raises(PollingTimeoutError):
        collection.build_from_config(config, timeout=0)


@patch("citrine.resources.gemtables.write_file_locally")
def test_read_table_from_collection(mock_write_files_locally, collection, table):
    # When
    with requests_mock.mock() as mock_get:
        remote_url = "http://otherhost:4572/anywhere"
        mock_get.get(remote_url, text='stuff')
        collection.read(table=table(remote_url), local_path="table.pdf")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 1
        assert mock_write_files_locally.call_args == call(b'stuff', "table.pdf")

    with requests_mock.mock() as mock_get:
        # When
        localstack_url = "http://localstack:4572/anywhere"
        mock_get.get("http://localhost:9572/anywhere", text='stuff')
        collection.read(table=table(localstack_url), local_path="table2.pdf")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 2
        assert mock_write_files_locally.call_args == call(b'stuff', "table2.pdf")

    with requests_mock.mock() as mock_get:
        # When
        localstack_url = "http://localstack:4572/anywhere"
        override_url = "https://fakestack:1337"
        collection.session.s3_endpoint_url = override_url
        mock_get.get(override_url + "/anywhere", text='stuff')
        collection.read(table=table(localstack_url), local_path="table3.pdf")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 3
        assert mock_write_files_locally.call_args == call(b'stuff', "table3.pdf")

    with requests_mock.mock() as mock_get:
        # When
        localstack_url = "http://localstack:4572/anywhere"
        override_url = "https://fakestack:1337"
        collection.session.s3_endpoint_url = override_url
        mock_get.get(override_url + "/anywhere", text='stuff')
        this_table = table(localstack_url)
        collection.session.set_response({"tables": [this_table.dump()]})
        collection.read(table=this_table.uid, local_path="table4.pdf")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 4
        assert mock_write_files_locally.call_args == call(b'stuff', "table4.pdf")


@patch("citrine.resources.gemtables.write_file_locally")
@pytest.mark.filterwarnings("ignore:A tuple*:DeprecationWarning")
def test_get_and_read_table_from_collection(mock_write_files_locally, table, session, collection):
    with requests_mock.mock() as mock_get:
        # Given
        remote_url = "http://otherhost:4572/anywhere"
        retrieved_table = table(remote_url)
        print(retrieved_table.dump())
        session.set_response(retrieved_table.dump())
        mock_get.get(remote_url, text='stuff')
        collection.read(table=(retrieved_table.uid, retrieved_table.version), local_path="table4.csv")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 1
        assert mock_write_files_locally.call_args == call(b'stuff', "table4.csv")


def test_read_table_into_memory_from_collection(table, session, collection):
    with requests_mock.mock() as mock_get:
        # Given
        remote_url = "http://otherhost:4572/anywhere"
        content = "stuff"
        retrieved_table = table(remote_url)
        session.set_response(retrieved_table.dump())
        mock_get.get(remote_url, text=content)
        returned = collection.read_to_memory(retrieved_table)
        assert mock_get.call_count == 1
        assert returned == content


def test_gem_table_entity_dict():
    table = GemTable.build(GemTableDataFactory())
    entity = table.access_control_dict()

    assert entity == {
        'id': str(table.uid),
        'type': 'TABLE'
    }
