"""Tests predictor collection"""
import mock
import pytest
import uuid
from copy import deepcopy

from citrine.exceptions import BadRequest, Conflict, ModuleRegistrationFailedException, NotFound
from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.predictors import (
    AutoMLPredictor,
    ExpressionPredictor,
    GraphPredictor,
    SimpleMixturePredictor
)
from citrine.resources.predictor import PredictorCollection, _PredictorVersionCollection, AutoConfigureMode
from tests.conftest import build_predictor_entity
from tests.utils.session import (
    FakeCall,
    FakeRequestResponse,
    FakeSession
)
from tests.utils.factories import (
        AsyncDefaultPredictorResponseFactory, AsyncDefaultPredictorResponseMetadataFactory,
        TableDataSourceDataFactory
)


def paging_response(*items):
    return {"response": items}


@pytest.fixture(scope='module')
def basic_predictor_report_data():
    return {
        'id': str(uuid.uuid4()),
        'status': 'VALID',
        'report': {'descriptors': [], 'models': []}
    }


def test_build(valid_graph_predictor_data, basic_predictor_report_data):
    session = FakeSession()
    session.set_response(basic_predictor_report_data)
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_graph_predictor_data)
    assert predictor.name == 'Graph predictor'
    assert predictor.description == 'description'


def test_build_with_status(valid_graph_predictor_data, basic_predictor_report_data):
    session = FakeSession()
    session.set_response(basic_predictor_report_data)

    status_detail_data = {("Info", "info_msg"), ("Warning", "warning msg"), ("Error", "error msg")}
    data = deepcopy(valid_graph_predictor_data)
    data["metadata"]["status"]["detail"] = [{"level": level, "msg": msg} for level, msg in status_detail_data]

    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(data)

    status_detail_tuples = {(detail.level, detail.msg) for detail in predictor.status_detail}
    assert status_detail_tuples == status_detail_data


def test_delete():
    pc = PredictorCollection(uuid.uuid4(), mock.Mock())
    with pytest.raises(NotImplementedError):
        pc.delete(uuid.uuid4())


def test_archive_root(valid_graph_predictor_data):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    predictors_path = PredictorCollection._path_template.format(project_id=pc.project_id)
    pred_id = valid_graph_predictor_data["id"]

    session.set_response(None)

    pc.archive_root(pred_id)

    assert session.calls == [FakeCall(method='PUT', path=f"{predictors_path}/{pred_id}/archive", json={})]


def test_restore_root(valid_graph_predictor_data):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    predictors_path = PredictorCollection._path_template.format(project_id=pc.project_id)
    pred_id = valid_graph_predictor_data["id"]

    session.set_response(None)

    pc.restore_root(pred_id)

    assert session.calls == [FakeCall(method='PUT', path=f"{predictors_path}/{pred_id}/restore", json={})]


def test_root_is_archived(valid_graph_predictor_data):
    predictor_id = uuid.UUID(valid_graph_predictor_data["id"])

    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    session.set_response(paging_response(valid_graph_predictor_data))

    assert pc.root_is_archived(predictor_id)
    assert pc.root_is_archived(str(predictor_id))
    assert not pc.root_is_archived(uuid.uuid4())
    assert not pc.root_is_archived(str(uuid.uuid4()))

    session.set_response(paging_response())

    assert not pc.root_is_archived(predictor_id)


def test_graph_build(valid_graph_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_graph_predictor_data)
    assert predictor.name == 'Graph predictor'
    assert predictor.description == 'description'
    assert len(predictor.predictors) == 5
    assert len(predictor.training_data) == 1


def test_register(valid_graph_predictor_data):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    entity = deepcopy(valid_graph_predictor_data)
    session.set_response(entity)

    predictor = pc.build(entity)

    predictors_path = f"/projects/{pc.project_id}/predictors"
    expected_calls = [
        FakeCall(method="POST", path=predictors_path, json=predictor.dump()),
        FakeCall(method="PUT", path=f"{predictors_path}/{entity['id']}/train", params={"create_version": True}, json={}),
    ]

    updated_predictor = pc.register(predictor)

    assert session.calls == expected_calls


def test_graph_register(valid_graph_predictor_data):
    pred_data = deepcopy(valid_graph_predictor_data)

    session = FakeSession()
    session.set_responses(deepcopy(valid_graph_predictor_data), pred_data)
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = GraphPredictor.build(valid_graph_predictor_data)
    registered = pc.register(predictor)
    
    assert registered.name == 'Graph predictor'


def test_failed_register(valid_graph_predictor_data):
    session = mock.Mock()
    session.post_resource.side_effect = NotFound("/projects/uuid/not_found",
                                                 FakeRequestResponse(400))
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = GraphPredictor.build(valid_graph_predictor_data)
    with pytest.raises(ModuleRegistrationFailedException) as e:
        pc.register(predictor)
    assert 'The "GraphPredictor" failed to register.' in str(e.value)
    assert '/projects/uuid/not_found' in str(e.value)


def test_update(valid_graph_predictor_data):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    entity = deepcopy(valid_graph_predictor_data)
    session.set_response(entity)

    predictor = pc.build(entity)

    predictors_path = PredictorCollection._path_template.format(project_id=pc.project_id)
    entity_path = f"{predictors_path}/{entity['id']}"
    expected_calls = [
        FakeCall(method="PUT", path=entity_path, json=predictor.dump()),
        FakeCall(method="PUT", path=f"{entity_path}/train", params={"create_version": True}, json={}),
    ]

    updated_predictor = pc.update(predictor)

    assert session.calls == expected_calls


def test_register_update_checks_status(valid_graph_predictor_data):
    # PredictorCollection.register/update makes two calls internally
    # The first creates/updates the resource, the second kicks off training
    # Test if create/update returns an INVALID status, we don't make the training call
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)

    instance = deepcopy(valid_graph_predictor_data)["data"]["instance"]
    valid_entity = build_predictor_entity(instance)
    invalid_entity = build_predictor_entity(
        instance,
        status_name="INVALID",
        status_detail=[{"level": "Error", "msg": "AHH IT BURNSSSSS!!!!"}]
    )

    # Register returns first (invalid) response if failed
    session.set_responses(invalid_entity, valid_entity)
    register_input = pc.build(valid_entity)
    register_output = pc.register(register_input)
    assert register_output.failed()
    assert session.num_calls == 1

    # Update returns first (invalid) response if failed
    session.set_responses(invalid_entity, valid_entity)
    update_input = pc.build(valid_entity)
    update_output = pc.update(update_input)
    assert update_output.failed()
    assert session.num_calls == 2


def test_list_predictors(valid_graph_predictor_data, valid_graph_predictor_data_empty):
    # Given
    session = FakeSession()
    collection = PredictorCollection(uuid.uuid4(), session)
    session.set_responses(
        {
            'response': [valid_graph_predictor_data, valid_graph_predictor_data_empty],
            'next': ''
        },
        basic_predictor_report_data,
        basic_predictor_report_data
    )

    # When
    predictors = list(collection.list(per_page=20))

    # Then
    expected_call = FakeCall(method='GET', path='/projects/{}/predictors'.format(collection.project_id),
                                   params={'per_page': 20, 'page': 1})
    assert 1 == session.num_calls, session.calls
    assert expected_call == session.calls[0]
    assert len(predictors) == 2


def test_get(valid_graph_predictor_data):
    # Given
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    entity = valid_graph_predictor_data
    session.set_responses(entity)
    id = uuid.uuid4()
    version = 4

    # When
    pc.get(id, version=version)

    # Then
    expected_call = FakeCall(
        method='GET',
        path=f'/projects/{pc.project_id}/predictors/{id}/versions/{version}',
        params={}
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call


def test_get_none():
    """Trying to get a predictor with uid=None should result in an informative error."""
    pc = PredictorCollection(uuid.uuid4(), FakeSession())

    with pytest.raises(ValueError) as excinfo:
        pc.get(uid=None)

    assert "uid=None" in str(excinfo.value)


def test_check_update_none():
    """Test that check-for-updates makes the expected calls, parses output for no update."""
    # Given
    session = FakeSession()
    session.set_response({"updatable": False})
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor_id = uuid.uuid4()

    # when
    update_check = pc.check_for_update(predictor_id)

    # then
    assert update_check is None
    expected_call = FakeCall(method='GET', path='/projects/{}/predictors/{}/update-check'.format(pc.project_id, predictor_id))
    assert session.calls[0] == expected_call


def test_check_update_some():
    """Test the update check correctly builds a module."""
    # given
    session = FakeSession()
    desc = RealDescriptor("spam", lower_bound=0, upper_bound=1, units="kg")
    response = GraphPredictor.wrap_instance({
        "type": "Graph",
        "name": "foo",
        "description": "bar",
        "predictors": [
            {
                "type": "AnalyticExpression",
                "name": "foo",
                "description": "bar",
                "expression": "2 * x",
                "output": RealDescriptor("spam", lower_bound=0, upper_bound=1, units="kg").dump(),
                "aliases": {}
            }
        ]
    })
    session.set_responses({"updatable": True, **response})
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor_id = uuid.uuid4()

    # when
    update_check = pc.check_for_update(predictor_id)

    # then
    assert pc._api_version == 'v3'
    exp = ExpressionPredictor("foo", description="bar", expression="2 * x", output=desc, aliases={})
    expected = GraphPredictor(
        name="foo",
        description="bar",
        predictors=[exp]
    )
    assert update_check.dump() == expected.dump()
    assert update_check.uid == predictor_id


def test_unexpected_pattern():
    """Check that unexpected patterns result in a value error"""
    # Given
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)

    # Then
    with pytest.raises(ValueError):
        pc.create_default(training_data=GemTableDataSource(table_id=uuid.uuid4(), table_version=0), pattern="yogurt")
    with pytest.raises(ValueError):
        pc.create_default_async(training_data=GemTableDataSource(table_id=uuid.uuid4(), table_version=0), pattern="yogurt")


def test_create_default_mode_pattern(valid_graph_predictor_data):
    """Check that using AutoConfigureMode doesn't result in an error"""
    # Given

    session = FakeSession()
    # Setup a response that includes instance instead of config
    response = deepcopy(valid_graph_predictor_data)
    session.set_response(response["data"])

    pc = PredictorCollection(uuid.uuid4(), session)

    # When
    pc.create_default(training_data=GemTableDataSource(table_id=uuid.uuid4(), table_version=0), pattern=AutoConfigureMode.INFER)

    # Then
    assert (session.calls[0].json['pattern'] == "INFER")
    assert (session.calls[0].json['prefer_valid'] == True)


def test_returned_predictor(valid_graph_predictor_data):
    """Check that create_default works on the happy path."""
    # Given
    session = FakeSession()

    # Setup a response that includes instance instead of config
    response = deepcopy(valid_graph_predictor_data)["data"]

    session.set_responses(response)
    pc = PredictorCollection(uuid.uuid4(), session)

    # When
    result = pc.create_default(training_data=GemTableDataSource(table_id=uuid.uuid4(), table_version=0), pattern="PLAIN")

    # Then the response is parsed in a predictor
    assert result.name == valid_graph_predictor_data["data"]["name"]
    assert isinstance(result, GraphPredictor)
    # including nested predictors
    assert len(result.predictors) == 5
    assert isinstance(result.predictors[0], SimpleMixturePredictor)
    assert isinstance(result.predictors[-1], AutoMLPredictor)


@pytest.mark.parametrize("version", (2, "1", "latest", "most_recent", None))
def test_convert_to_graph(valid_graph_predictor_data, version):
    # Given
    project_id = uuid.uuid4()
    session = FakeSession()
    collection = PredictorCollection(project_id, session)

    # Building a predictor may modify the input data object, which interferes with the test
    # input later in the test. By making a copy, we don't need to care if the input is mutated.
    predictor = collection.build(deepcopy(valid_graph_predictor_data))

    session.set_response(deepcopy(valid_graph_predictor_data))

    versions_path = _PredictorVersionCollection._path_template.format(project_id=collection.project_id, uid=predictor.uid)
    entity_path = f"{versions_path}/{version or 'most_recent'}"

    # When
    kwargs = {"version": version} if version is not None else {}
    response = collection.convert_to_graph(predictor.uid, **kwargs)

    # Then
    assert session.calls == [FakeCall(method="GET", path=f"{entity_path}/convert")]
    assert response.dump() == predictor.dump()


@pytest.mark.parametrize("version", (2, "1", "latest", "most_recent", None))
def test_convert_and_update(valid_graph_predictor_data, version):
    # Given
    project_id = uuid.uuid4()
    predictor_id = valid_graph_predictor_data["id"]
    session = FakeSession()
    collection = PredictorCollection(project_id, session)

    # Building a graph predictor modifies the input data object, which interferes with the test
    # input later in the test. By making a copy, we don't need to care if the input is mutated.
    predictor = collection.build(deepcopy(valid_graph_predictor_data))

    session.set_responses(deepcopy(valid_graph_predictor_data), deepcopy(valid_graph_predictor_data), deepcopy(valid_graph_predictor_data))

    predictors_path = PredictorCollection._path_template.format(project_id=project_id)
    versions_path = _PredictorVersionCollection._path_template.format(project_id=collection.project_id, uid=predictor.uid)
    root_path = f"{predictors_path}/{predictor_id}"
    entity_path = f"{versions_path}/{version or 'most_recent'}"
    expected_calls = [
        FakeCall(method="GET", path=f"{entity_path}/convert"),
        FakeCall(method="PUT", path=root_path, json=predictor.dump()),
        FakeCall(method="PUT", path=f"{root_path}/train", params={"create_version": True}, json={}),
    ]

    # When
    kwargs = {"version": version} if version is not None else {}
    response = collection.convert_and_update(predictor.uid, **kwargs)

    # Then
    assert session.calls == expected_calls
    assert response.dump() == predictor.dump()


@pytest.mark.parametrize("version", (2, "1", "latest", "most_recent", None))
@pytest.mark.parametrize("error_args", ((400, BadRequest), (409, Conflict)))
@pytest.mark.parametrize("method_name", ("convert_to_graph", "convert_and_update"))
def test_convert_and_update_errors(version, error_args, method_name):
    # Given
    project_id = uuid.uuid4()
    predictor_id = uuid.uuid4()
    session = FakeSession()
    collection = PredictorCollection(project_id, session)
    convert_path = f"/projects/{project_id}/predictors/{predictor_id}/versions/{version or 'most_recent'}/convert"

    error_code, error_cls = error_args[:]
    response = FakeRequestResponse(error_code)
    response.request.method = "GET"
    session.set_response(error_cls(convert_path, response))

    # When
    kwargs = {"version": version} if version is not None else {}
    method = getattr(collection, method_name)
    with pytest.raises(error_cls):
        method(predictor_id, **kwargs)

    # Then
    assert session.num_calls == 1
    expected_call_convert = FakeCall(method="GET", path=convert_path)
    assert session.last_call == expected_call_convert


@pytest.mark.parametrize("version", (2, "1", "latest", "most_recent", None))
@pytest.mark.parametrize("method_name", ("convert_to_graph", "convert_and_update"))
def test_convert_auto_retrain(valid_graph_predictor_data, version, method_name):
    # Given
    project_id = uuid.uuid4()
    predictor_id = valid_graph_predictor_data["id"]
    session = FakeSession()
    collection = PredictorCollection(project_id, session)
    predictors_path = collection._path_template.format(project_id=project_id)
    version_path = f"{predictors_path}/{predictor_id}/versions/{version or 'most_recent'}"
    convert_path = f"{version_path}/convert"
    train_path = f"{version_path}/train"

    # Building a graph predictor modifies the input data object, which interferes with the test
    # input later in the test. By making a copy, we don't need to care if the input is mutated.
    predictor = collection.build(deepcopy(valid_graph_predictor_data))

    response = FakeRequestResponse(409)
    response.request.method = "GET"

    session.set_responses(
        Conflict(convert_path, response),
        deepcopy(valid_graph_predictor_data)
    )

    # When
    method = getattr(collection, method_name)
    kwargs = {"version": version} if version is not None else {}
    response = method(predictor_id, retrain_if_needed=True, **kwargs)

    # Then
    expected_calls = [
        FakeCall(method="GET", path=convert_path),
        FakeCall(method="PUT", path=train_path, params={"create_version": True}, json={}),
    ]
    assert session.calls == expected_calls
    assert response is None


def test_predictor_list_archived(valid_graph_predictor_data):
    # Given
    session = FakeSession()
    session.set_response({'response': [valid_graph_predictor_data]})
    pc = PredictorCollection(uuid.uuid4(), session)

    # When
    list(pc.list_archived())

    # Then
    assert session.num_calls == 1
    assert session.last_call == FakeCall(method='GET', path=f"/projects/{pc.project_id}/predictors", params={"filter": "archived eq 'true'", 'per_page': 20, 'page': 1})


def test_list_versions(valid_graph_predictor_data):
    # Given
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    pred_id = valid_graph_predictor_data["id"]

    predictor_v1 = deepcopy(valid_graph_predictor_data)
    predictor_v1["metadata"]["draft"] = False

    predictor_v2 = deepcopy(valid_graph_predictor_data)
    predictor_v2["metadata"]["version"] = 2

    versions_path = _PredictorVersionCollection._path_template.format(project_id=pc.project_id, uid=pred_id)

    session.set_response(paging_response(predictor_v1, predictor_v2))

    # When
    listed_predictors = list(pc.list_versions(pred_id, per_page=20))

    # Then
    assert session.calls == [FakeCall(method='GET', path=versions_path, params={'per_page': 20, 'page': 1})]
    assert len(listed_predictors) == 2


def test_list_archived_versions(valid_graph_predictor_data):
    # Given
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    pred_id = valid_graph_predictor_data["id"]

    predictor_v1 = deepcopy(valid_graph_predictor_data)
    predictor_v1["metadata"]["draft"] = False

    predictor_v2 = deepcopy(valid_graph_predictor_data)
    predictor_v2["metadata"]["version"] = 2

    versions_path = _PredictorVersionCollection._path_template.format(project_id=pc.project_id, uid=pred_id)

    session.set_response(paging_response(predictor_v1, predictor_v2))

    # When
    listed_predictors = list(pc.list_archived_versions(pred_id, per_page=20))

    # Then
    expected_params = {'per_page': 20, "filter": "archived eq 'true'", 'page': 1}
    assert session.calls == [FakeCall(method='GET', path=versions_path, params=expected_params)]
    assert len(listed_predictors) == 2


@pytest.mark.parametrize("version", (2, "1", "latest", "most_recent"))
def test_archive_version(valid_graph_predictor_data, version):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    pred_id = valid_graph_predictor_data["id"]

    versions_path = _PredictorVersionCollection._path_template.format(project_id=pc.project_id, uid=pred_id)

    session.set_response(valid_graph_predictor_data)

    pc.archive_version(pred_id, version=version)

    assert session.calls == [FakeCall(method='PUT', path=f"{versions_path}/{version}/archive", json={})]


@pytest.mark.parametrize("version", (2, "1", "latest", "most_recent"))
def test_restore_version(valid_graph_predictor_data, version):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    pred_id = valid_graph_predictor_data["id"]

    versions_path = _PredictorVersionCollection._path_template.format(project_id=pc.project_id, uid=pred_id)

    session.set_response(valid_graph_predictor_data)

    pc.restore_version(pred_id, version=version)

    assert session.calls == [FakeCall(method='PUT', path=f"{versions_path}/{version}/restore", json={})]


@pytest.mark.parametrize("version", (-2, 0, "1.5", "draft"))
def test_archive_invalid_version(valid_graph_predictor_data, version):
    session = FakeSession()
    session.set_response(valid_graph_predictor_data)
    pc = PredictorCollection(uuid.uuid4(), session)

    with pytest.raises(ValueError):
        pc.archive_version(uuid.uuid4(), version=version)


@pytest.mark.parametrize("version", (-2, 0, "1.5", "draft"))
def test_restore_invalid_version(valid_graph_predictor_data, version):
    session = FakeSession()
    session.set_response(valid_graph_predictor_data)
    pc = PredictorCollection(uuid.uuid4(), session)

    with pytest.raises(ValueError):
        pc.restore_version(uuid.uuid4(), version=version)


@pytest.mark.parametrize("is_stale", (True, False))
def test_is_stale(valid_graph_predictor_data, is_stale):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    pred_id = valid_graph_predictor_data["id"]
    pred_version = valid_graph_predictor_data["metadata"]["version"]
    response = {
        "id": pred_id,
        "version": pred_version,
        "status": "READY",
        "is_stale": is_stale
    }
    session.set_response(response)

    resp = pc.is_stale(pred_id, version=pred_version)

    versions_path = _PredictorVersionCollection._path_template.format(project_id=pc.project_id, uid=pred_id)
    assert session.calls == [FakeCall(method='GET', path=f"{versions_path}/{pred_version}/is-stale")]
    assert resp == is_stale

def test_retrain_stale(valid_graph_predictor_data):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    pred_id = valid_graph_predictor_data["id"]
    pred_version = valid_graph_predictor_data["metadata"]["version"]

    response = deepcopy(valid_graph_predictor_data)
    response["metadata"]["status"]["name"] = "VALIDATING"
    response["metadata"]["status"]["detail"] = []
    session.set_response(response)

    pc.retrain_stale(pred_id, version=pred_version)

    versions_path = _PredictorVersionCollection._path_template.format(project_id=pc.project_id, uid=pred_id)
    assert session.calls == [FakeCall(method='PUT', path=f"{versions_path}/{pred_version}/retrain-stale", json={})]

def test_unsupported_archive():
    with pytest.raises(NotImplementedError):
        PredictorCollection(uuid.uuid4(), FakeSession()).archive(uuid.uuid4())

def test_unsupported_restore():
    with pytest.raises(NotImplementedError):
        PredictorCollection(uuid.uuid4(), FakeSession()).restore(uuid.uuid4())

def test_create_default_async():
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    predictors_path = PredictorCollection._path_template.format(project_id=pc.project_id)
        
    mode = "PLAIN"
    prefer_valid = False
    ds = GemTableDataSource(table_id=uuid.uuid4(), table_version=1)
    data_source_payload = TableDataSourceDataFactory(table_id=str(ds.table_id), table_version=ds.table_version)
    expected_payload = {
        "data_source": data_source_payload,
        "pattern": mode,
        "prefer_valid": prefer_valid
    }

    metadata = AsyncDefaultPredictorResponseMetadataFactory(data_source=data_source_payload)
    session.set_response(AsyncDefaultPredictorResponseFactory(metadata=metadata, data=None))

    result = pc.create_default_async(training_data=ds, pattern=mode, prefer_valid=prefer_valid)

    assert session.calls == [FakeCall(method="POST", path=f"{predictors_path}/default-async", json=expected_payload)]


def test_get_default_async(valid_graph_predictor_data):
    instance = valid_graph_predictor_data["data"]["instance"]
    # Given
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)

    response = AsyncDefaultPredictorResponseFactory()
    response["data"]["instance"] = instance
    session.set_response(response)

    # When
    result = pc.get_default_async(task_id=response["id"])

    # Then the response is parsed in a predictor
    assert str(result.uid) == response["id"]
    assert result.status == response["metadata"]["status"]
    assert result.status_detail == response["metadata"]["status_detail"]
    assert result.predictor is not None
    assert result.predictor.predictors
    assert len(result.predictor.predictors) == len(instance["predictors"])


def test_get_featurized_training_data(example_hierarchical_design_material):
    # Given
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    session.set_responses([example_hierarchical_design_material])
    id = uuid.uuid4()
    version = 4

    # When
    materials = pc.get_featurized_training_data(id, version=version)

    # Then
    expected_call = FakeCall(
        method='GET',
        path=f'/projects/{pc.project_id}/predictors/{id}/versions/{version}/featurized-training-data',
        params={}
    )
    assert session.num_calls == 1
    assert expected_call == session.last_call
    assert len(materials) == 1
