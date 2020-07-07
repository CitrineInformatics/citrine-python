from uuid import UUID

import pytest
import requests_mock
from mock import patch, call

from citrine.resources.table import TableCollection, Table
from tests.utils.factories import TableDataFactory, ListTableVersionsDataFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> TableCollection:
    return TableCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        session=session
    )


@pytest.fixture
def table() -> Table:
    def _table(download_url: str):
        return Table.build(TableDataFactory(signed_download_url=download_url, version=2))

    return _table


@patch("citrine.resources.table.write_file_locally")
def test_read_table(mock_write_files_locally, table):
    # When
    with requests_mock.mock() as mock_get:
        remote_url = "http://otherhost:4572/anywhere"
        mock_get.get(remote_url, text='stuff')
        table(remote_url).read("table.pdf")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 1
        assert mock_write_files_locally.call_args == call(b'stuff', "table.pdf")

    with requests_mock.mock() as mock_get:
        # When
        localstack_url = "http://localstack:4572/anywhere"
        mock_get.get("http://localhost:9572/anywhere", text='stuff')
        table(localstack_url).read("table2.pdf")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 2
        assert mock_write_files_locally.call_args == call(b'stuff', "table2.pdf")


def test_get_table_metadata(collection, session):
    # Given
    project_id = '6b608f78-e341-422c-8076-35adc8828545'
    table = TableDataFactory()
    session.set_response(table)

    # When
    retrieved_table: Table = collection.get(table["id"], table["version"])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="GET",
        path="projects/{}/display-tables/{}/versions/{}".format(project_id, table["id"], table["version"])
    )
    assert session.last_call == expect_call
    assert str(retrieved_table.uid) == table["id"]
    assert retrieved_table.version == table["version"]
    assert retrieved_table.download_url == table["signed_download_url"]


def test_list_tables(collection, session):
    # Given
    tableVersions = ListTableVersionsDataFactory()
    session.set_response(tableVersions)

    # When
    results = list(collection.list())

    # Then
    assert len(results) == 1
    assert results[0].uid is not None


def test_list_table_versions(collection, session):
    # Given
    tableVersions = ListTableVersionsDataFactory()
    session.set_response(tableVersions)

    # When
    results = list(collection.list_versions(tableVersions['tables'][0]['id']))

    # Then
    assert len(results) == 1
    assert results[0].uid is not None


def test_list_by_config(collection, session):
    # Given
    tableVersions = ListTableVersionsDataFactory()
    session.set_response(tableVersions)

    # When
    # NOTE: list_by_config returns slightly more info in this call, but it's a superset of
    # a typical Table, and parsed identically in citrine-python.
    results = list(collection.list_by_config(tableVersions['tables'][0]['id']))

    # Then
    assert len(results) == 1
    assert results[0].uid is not None


def test_init_table():
    table = Table()
    assert table.uid is None
    assert table.version is None
    assert table.download_url is None


def test_str_serialization(table):
    t = table("http://somewhere.cool")
    assert str(t) == "<Table {!r}, version {}>".format(t.uid, 2)


def test_register_table(collection):
    with pytest.raises(RuntimeError):
        collection.register(Table.build(TableDataFactory()))


@patch("citrine.resources.table.write_file_locally")
def test_read_table_from_collection(mock_write_files_locally, collection, table):
    # When
    with requests_mock.mock() as mock_get:
        remote_url = "http://otherhost:4572/anywhere"
        mock_get.get(remote_url, text='stuff')
        collection.read(table(remote_url), "table.pdf")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 1
        assert mock_write_files_locally.call_args == call(b'stuff', "table.pdf")

    with requests_mock.mock() as mock_get:
        # When
        localstack_url = "http://localstack:4572/anywhere"
        mock_get.get("http://localhost:9572/anywhere", text='stuff')
        collection.read(table(localstack_url), "table2.pdf")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 2
        assert mock_write_files_locally.call_args == call(b'stuff', "table2.pdf")

    with requests_mock.mock() as mock_get:
        # When
        localstack_url = "http://localstack:4572/anywhere"
        override_url = "https://fakestack:1337"
        collection.session.s3_endpoint_url = override_url
        mock_get.get(override_url + "/anywhere", text='stuff')
        collection.read(table(localstack_url), "table3.pdf")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 3
        assert mock_write_files_locally.call_args == call(b'stuff', "table3.pdf")


@patch("citrine.resources.table.write_file_locally")
def test_get_and_read_table_from_collection(mock_write_files_locally, table, session, collection):
    with requests_mock.mock() as mock_get:
        # Given
        remote_url = "http://otherhost:4572/anywhere"
        retrieved_table = table(remote_url)
        session.set_response(retrieved_table.dump())
        mock_get.get(remote_url, text='stuff')
        collection.read((retrieved_table.uid, retrieved_table.version), "table4.csv")
        assert mock_get.call_count == 1
        assert mock_write_files_locally.call_count == 1
        assert mock_write_files_locally.call_args == call(b'stuff', "table4.csv")
