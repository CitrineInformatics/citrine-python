import csv
import io
import json
import uuid

import pytest

from citrine.resources.experiment_datasource import ExperimentDataSource, ExperimentDataSourceCollection
from tests.utils.factories import ExperimentDataSourceDataFactory
from tests.utils.session import (
    FakeCall,
    FakeSession
)


LATEST_VER = "latest"


@pytest.fixture
def session():
    return FakeSession()


@pytest.fixture
def collection(session) -> ExperimentDataSourceCollection:
    return ExperimentDataSourceCollection(uuid.uuid4(), session)


@pytest.fixture
def erds_base_path(collection):
    return f'projects/{collection.project_id}/candidate-experiment-datasources'


def assert_erds_csv(erds_csv, erds_dict):
    for row, expt in zip(csv.DictReader(io.StringIO(erds_csv)), erds_dict["data"]["experiments"]):
        for variable, actual_value_raw in row.items():
            assert expt["overrides"][variable]["value"] == json.loads(actual_value_raw)


def test_build(collection):
    erds_dict = ExperimentDataSourceDataFactory()
    actual_erds: ExperimentDataSource = collection.build(erds_dict)

    assert str(actual_erds.uid) == erds_dict["id"]
    assert str(actual_erds.branch_root_id) == erds_dict["metadata"]["branch_root_id"]
    assert actual_erds.version == erds_dict["metadata"]["version"]
    assert str(actual_erds.created_by) == erds_dict["metadata"]["created"]["user"]
    # TODO: It'd be better to actually invoke the Datetime._serialize method
    assert int(actual_erds.create_time.timestamp() * 1000 + 0.0001) == erds_dict["metadata"]["created"]["time"]

    for actual_experiment, erds_experiment in zip(actual_erds.experiments, erds_dict["data"]["experiments"]):
        assert str(actual_experiment.uid) == erds_experiment["experiment_id"]
        assert str(actual_experiment.candidate_id) == erds_experiment["candidate_id"]
        assert str(actual_experiment.workflow_id) == erds_experiment["workflow_id"]
        assert actual_experiment.name == erds_experiment["name"]
        assert actual_experiment.description == erds_experiment["description"]
        # TODO: It'd be better to actually invoke the Datetime._serialize method
        assert int(actual_experiment.updated_time.timestamp() * 1000 + 0.0001) == erds_experiment["updated_time"]

        for actual_override, erds_override in zip(actual_experiment.overrides.items(), erds_experiment["overrides"].items()):
            actual_override_key, actual_override_value = actual_override
            erds_override_key, erds_override_value = erds_override
            assert actual_override_key == erds_override_key
            assert actual_override_value.typ == erds_override_value["type"]
            assert actual_override_value.value == erds_override_value["value"]


def test_list(session, collection, erds_base_path):
    version_id = uuid.uuid4()

    session.set_response({"response": []})

    list(collection.list())
    list(collection.list(branch_version_id=version_id))
    list(collection.list(version=4))
    list(collection.list(version=LATEST_VER))
    list(collection.list(branch_version_id=version_id, version=12))
    list(collection.list(branch_version_id=version_id, version=LATEST_VER))

    assert session.calls == [
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, 'page': 1}),
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, "branch": str(version_id), 'page': 1}),
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, "version": 4, 'page': 1}),
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, "version": LATEST_VER, 'page': 1}),
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, "branch": str(version_id), "version": 12, 'page': 1}),
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, "branch": str(version_id), "version": LATEST_VER, 'page': 1})
    ]


def test_read_and_retrieve(session, collection, erds_base_path):
    erds_dict = ExperimentDataSourceDataFactory()
    erds_id = uuid.uuid4()
    erds_path = f"{erds_base_path}/{erds_id}"

    session.set_response(erds_dict)

    erds_csv = collection.read(erds_id)

    assert session.calls == [FakeCall(method='GET', path=erds_path)]
    assert_erds_csv(erds_csv, erds_dict)


def test_read_from_obj(session, collection):
    erds_dict = ExperimentDataSourceDataFactory()
    erds_obj = collection.build(erds_dict)

    erds_csv = collection.read(erds_obj)

    assert not session.calls
    assert_erds_csv(erds_csv, erds_dict)
