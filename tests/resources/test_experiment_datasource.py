import csv
import io
import json
import uuid

import pytest

from citrine.informatics.experiment_values import CategoricalExperimentValue, \
                                                  ChemicalFormulaExperimentValue, \
                                                  IntegerExperimentValue, \
                                                  MixtureExperimentValue, \
                                                  MolecularStructureExperimentValue, \
                                                  RealExperimentValue
from citrine.resources.experiment_datasource import ExperimentDataSourceCollection
from tests.utils.factories import CandidateExperimentSnapshotDataFactory, \
                                  CategoricalExperimentValueDataFactory, \
                                  ChemicalFormulaExperimentValueDataFactory, \
                                  ExperimentDataSourceDataDataFactory, \
                                  ExperimentDataSourceDataFactory, \
                                  IntegerExperimentValueDataFactory, \
                                  MixtureExperimentValueDataFactory, \
                                  MolecularStructureExperimentValueDataFactory, \
                                  RealExperimentValueDataFactory
from tests.utils.session import (
    FakeCall,
    FakeRequest,
    FakeRequestResponse,
    FakeSession
)


@pytest.fixture
def session():
    return FakeSession()


@pytest.fixture
def collection(session):
    return ExperimentDataSourceCollection(uuid.uuid4(), session)


@pytest.fixture
def erds_base_path(collection):
    return f'projects/{collection.project_id}/candidate-experiment-datasources'


@pytest.fixture
def erds_dict():
    overrides = {
        "ingredient1": CategoricalExperimentValueDataFactory(),
        "ingredient2": ChemicalFormulaExperimentValueDataFactory(value="(Ca)1(O)3(Si)1"),
        "ingredient3": IntegerExperimentValueDataFactory(),
        "Formulation": MixtureExperimentValueDataFactory(value={"ingredient1": 0.3, "ingredient2": 0.7}),
        "ingredient4": MolecularStructureExperimentValueDataFactory(value="CC1(CC(CC(N1)(C)C)NCCCCCCNC2CC(NC(C2)(C)C)(C)C)C.C1COCCN1C2=NC(=NC(=N2)Cl)Cl"),
        "ingredient5": RealExperimentValueDataFactory()
    }
    experiments = [CandidateExperimentSnapshotDataFactory(overrides=overrides)]
    data = ExperimentDataSourceDataDataFactory(experiments=experiments)
    return ExperimentDataSourceDataFactory(data=data)


def assert_erds_csv(erds_csv, erds_dict):
    for row, expt in zip(csv.DictReader(io.StringIO(erds_csv)), erds_dict["data"]["experiments"]):
        for variable, actual_value_raw in row.items():
            assert expt["overrides"][variable]["value"] == json.loads(actual_value_raw)


def test_build(collection, erds_dict):
    actual_erds = collection.build(erds_dict)

    assert str(actual_erds.uid) == erds_dict["id"]
    assert str(actual_erds.branch_root_id) == erds_dict["metadata"]["branch_root_id"]
    assert actual_erds.version == erds_dict["metadata"]["version"]
    assert str(actual_erds.created_by) == erds_dict["metadata"]["created"]["user"]
    assert actual_erds.create_time.replace(tzinfo=None).isoformat() == erds_dict["metadata"]["created"]["time"]

    for actual_experiment, erds_experiment in zip(actual_erds.experiments, erds_dict["data"]["experiments"]):
        assert str(actual_experiment.uid) == erds_experiment["experiment_id"]
        assert str(actual_experiment.candidate_id) == erds_experiment["candidate_id"]
        assert str(actual_experiment.workflow_id) == erds_experiment["workflow_id"]
        assert actual_experiment.name == erds_experiment["name"]
        assert actual_experiment.description == erds_experiment["description"]
        assert actual_experiment.updated_time.replace(tzinfo=None).isoformat() == erds_experiment["updated_time"]

        for actual_override, erds_override in zip(actual_experiment.overrides.items(), erds_experiment["overrides"].items()):
            actual_override_key, actual_override_value = actual_override
            erds_override_key, erds_override_value = erds_override
            assert actual_override_key == erds_override_key
            assert actual_override_value.typ == erds_override_value["type"]
            assert actual_override_value.value == erds_override_value["value"]


def test_list(session, collection, erds_base_path):

    branch_id = uuid.uuid4()

    session.set_response({"response": []})
    
    list(collection.list())
    list(collection.list(branch_id=branch_id))
    list(collection.list(version=4))
    list(collection.list(version="latest"))
    list(collection.list(branch_id=branch_id, version=12))
    list(collection.list(branch_id=branch_id, version="latest"))

    assert session.calls == [
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100}),
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, "branch": branch_id}),
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, "version": 4}),
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, "version": "latest"}),
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, "branch": branch_id, "version": 12}),
        FakeCall(method='GET', path=erds_base_path, params={'per_page': 100, "branch": branch_id, "version": "latest"})
    ]


def test_read_and_retrieve(session, collection, erds_dict, erds_base_path):
    erds_id = uuid.uuid4()
    erds_path = f"{erds_base_path}/{erds_id}"

    session.set_response(erds_dict)

    erds_csv = collection.read(erds_id)

    assert session.calls == [FakeCall(method='GET', path=erds_path)]
    assert_erds_csv(erds_csv, erds_dict)


def test_read_from_obj(session, collection, erds_dict):
    erds_obj = collection.build(erds_dict)

    erds_csv = collection.read(erds_obj)

    assert not session.calls
    assert_erds_csv(erds_csv, erds_dict)
