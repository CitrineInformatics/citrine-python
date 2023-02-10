"""Tests predictor collection"""
import mock
import pytest
import uuid
from copy import deepcopy

from citrine.exceptions import ModuleRegistrationFailedException, NotFound
from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.predictors import (
    AutoMLPredictor,
    ExpressionPredictor,
    GraphPredictor,
    Predictor,
)
from citrine.resources.predictor import PredictorCollection, _PredictorVersionCollection, AutoConfigureMode
from tests.conftest import build_predictor_entity
from tests.utils.session import (
    FakeCall,
    FakeRequestResponse,
    FakeSession
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


def test_build(valid_auto_ml_predictor_data, basic_predictor_report_data):
    session = FakeSession()
    session.set_response(basic_predictor_report_data)
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_auto_ml_predictor_data)
    assert predictor.name == 'AutoML predictor'
    assert predictor.description == 'Predicts z from input x'


def test_build_with_status(valid_auto_ml_predictor_data, basic_predictor_report_data):
    session = FakeSession()
    session.set_response(basic_predictor_report_data)

    status_detail_data = {("Info", "info_msg"), ("Warning", "warning msg"), ("Error", "error msg")}
    data = deepcopy(valid_auto_ml_predictor_data)
    data["metadata"]["status"]["detail"] = [{"level": level, "msg": msg} for level, msg in status_detail_data]

    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(data)

    status_detail_tuples = {(detail.level, detail.msg) for detail in predictor.status_detail}
    assert status_detail_tuples == status_detail_data


def test_delete():
    pc = PredictorCollection(uuid.uuid4(), mock.Mock())
    with pytest.raises(NotImplementedError):
        pc.delete(uuid.uuid4())


def test_archive_root(valid_label_fractions_predictor_data):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    predictors_path = PredictorCollection._path_template.format(project_id=pc.project_id)
    pred_id = valid_label_fractions_predictor_data["id"]

    session.set_response(None)

    pc.archive_root(pred_id)

    assert session.calls == [FakeCall(method='PUT', path=f"{predictors_path}/{pred_id}/archive", json={})]


def test_restore_root(valid_label_fractions_predictor_data):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    predictors_path = PredictorCollection._path_template.format(project_id=pc.project_id)
    pred_id = valid_label_fractions_predictor_data["id"]

    session.set_response(None)

    pc.restore_root(pred_id)

    assert session.calls == [FakeCall(method='PUT', path=f"{predictors_path}/{pred_id}/restore", json={})]


def test_root_is_archived(valid_label_fractions_predictor_data):
    predictor_id = uuid.UUID(valid_label_fractions_predictor_data["id"])

    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    session.set_response(paging_response(valid_label_fractions_predictor_data))

    assert pc.root_is_archived(predictor_id)
    assert pc.root_is_archived(str(predictor_id))
    assert not pc.root_is_archived(uuid.uuid4())
    assert not pc.root_is_archived(str(uuid.uuid4()))

    session.set_response(paging_response())

    assert not pc.root_is_archived(predictor_id)


def test_automl_build(valid_auto_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_auto_ml_predictor_data)
    assert predictor.name == 'AutoML predictor'
    assert predictor.description == 'Predicts z from input x'


def test_graph_build(valid_graph_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_graph_predictor_data)
    assert predictor.name == 'Graph predictor'
    assert predictor.description == 'description'
    assert len(predictor.predictors) == 2
    assert len(predictor.training_data) == 1


def test_register(valid_label_fractions_predictor_data):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    entity = deepcopy(valid_label_fractions_predictor_data)
    session.set_response(entity)

    predictor = pc.build(entity)

    predictors_path = f"/projects/{pc.project_id}/predictors"
    expected_calls = [
        FakeCall(method="POST", path=predictors_path, json=predictor.dump()),
        FakeCall(method="PUT", path=f"{predictors_path}/{entity['id']}/train", params={"create_version": True}, json={}),
    ]

    updated_predictor = pc.register(predictor)

    assert session.calls == expected_calls


def test_automl_register(valid_auto_ml_predictor_data):
    pred_data = valid_auto_ml_predictor_data

    session = FakeSession()
    session.set_responses(pred_data, pred_data, paging_response(pred_data))
    
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = AutoMLPredictor.build(valid_auto_ml_predictor_data)
    registered = pc.register(predictor)

    assert registered.name == 'AutoML predictor'


def test_graph_register(valid_graph_predictor_data, valid_graph_predictor_data_response):
    pred_data = deepcopy(valid_graph_predictor_data_response)

    session = FakeSession()
    session.set_responses(
        deepcopy(valid_graph_predictor_data_response),
        pred_data,
        paging_response(pred_data))
    
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = GraphPredictor.build(valid_graph_predictor_data)
    registered = pc.register(predictor)
    
    assert registered.name == 'Graph predictor'


def test_failed_register(valid_auto_ml_predictor_data):
    session = mock.Mock()
    session.post_resource.side_effect = NotFound("/projects/uuid/not_found",
                                                 FakeRequestResponse(400))
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = AutoMLPredictor.build(valid_auto_ml_predictor_data)
    with pytest.raises(ModuleRegistrationFailedException) as e:
        pc.register(predictor)
    assert 'The "AutoMLPredictor" failed to register.' in str(e.value)
    assert '/projects/uuid/not_found' in str(e.value)


def test_update(valid_label_fractions_predictor_data):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    entity = deepcopy(valid_label_fractions_predictor_data)
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


def test_register_update_checks_status(valid_auto_ml_predictor_data):
    # PredictorCollection.register/update makes two calls internally
    # The first creates/updates the resource, the second kicks off training
    # Test if create/update returns an INVALID status, we don't make the training call
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)

    instance = deepcopy(valid_auto_ml_predictor_data)["data"]["instance"]
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


def test_list_predictors(valid_auto_ml_predictor_data, valid_expression_predictor_data,
                         basic_predictor_report_data):
    # Given
    session = FakeSession()
    collection = PredictorCollection(uuid.uuid4(), session)
    session.set_responses(
        {
            'response': [valid_auto_ml_predictor_data, valid_expression_predictor_data],
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


def test_get(valid_label_fractions_predictor_data):
    # Given
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    entity = valid_label_fractions_predictor_data
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
    response = Predictor.wrap_instance({
        "type": "AnalyticExpression",
        "name": "foo",
        "description": "bar",
        "expression": "2 * x",
        "output": RealDescriptor("spam", lower_bound=0, upper_bound=1, units="kg").dump(),
        "aliases": {}
    })
    session.set_responses({"updatable": True, **response}, paging_response(response))
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor_id = uuid.uuid4()

    # when
    update_check = pc.check_for_update(predictor_id)

    # then
    assert pc._api_version == 'v3'
    expected = ExpressionPredictor("foo", description="bar", expression="2 * x", output=desc, aliases={})
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


def test_create_default_mode_pattern(valid_graph_predictor_data):
    """Check that using AutoConfigureMode doesn't result in an error"""
    # Given

    session = FakeSession()
    # Setup a response that includes instance instead of config
    response = deepcopy(valid_graph_predictor_data)
    session.set_responses(response["data"], paging_response(response))

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

    session.set_responses(response, paging_response(response))
    pc = PredictorCollection(uuid.uuid4(), session)

    # When
    result = pc.create_default(training_data=GemTableDataSource(table_id=uuid.uuid4(), table_version=0), pattern="PLAIN")

    # Then the response is parsed in a predictor
    assert result.name == valid_graph_predictor_data["data"]["name"]
    assert isinstance(result, GraphPredictor)
    # including nested predictors
    assert len(result.predictors) == 2
    assert isinstance(result.predictors[0], uuid.UUID)
    assert isinstance(result.predictors[1], ExpressionPredictor)


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


def test_list_versions(valid_expression_predictor_data):
    # Given
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    pred_id = valid_expression_predictor_data["id"]

    predictor_v1 = deepcopy(valid_expression_predictor_data)
    predictor_v1["metadata"]["draft"] = False

    predictor_v2 = deepcopy(valid_expression_predictor_data)
    predictor_v2["metadata"]["version"] = 2

    versions_path = _PredictorVersionCollection._path_template.format(project_id=pc.project_id, uid=pred_id)

    session.set_response(paging_response(predictor_v1, predictor_v2))

    # When
    listed_predictors = list(pc.list_versions(pred_id, per_page=20))

    # Then
    assert session.calls == [FakeCall(method='GET', path=versions_path, params={'per_page': 20, 'page': 1})]
    assert len(listed_predictors) == 2


def test_list_archived_versions(valid_expression_predictor_data):
    # Given
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    pred_id = valid_expression_predictor_data["id"]

    predictor_v1 = deepcopy(valid_expression_predictor_data)
    predictor_v1["metadata"]["draft"] = False

    predictor_v2 = deepcopy(valid_expression_predictor_data)
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
def test_archive_version(valid_label_fractions_predictor_data, version):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    pred_id = valid_label_fractions_predictor_data["id"]

    versions_path = _PredictorVersionCollection._path_template.format(project_id=pc.project_id, uid=pred_id)

    session.set_response(valid_label_fractions_predictor_data)

    pc.archive_version(pred_id, version=version)

    assert session.calls == [FakeCall(method='PUT', path=f"{versions_path}/{version}/archive", json={})]


@pytest.mark.parametrize("version", (2, "1", "latest", "most_recent"))
def test_restore_version(valid_label_fractions_predictor_data, version):
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)
    pred_id = valid_label_fractions_predictor_data["id"]

    versions_path = _PredictorVersionCollection._path_template.format(project_id=pc.project_id, uid=pred_id)

    session.set_response(valid_label_fractions_predictor_data)

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
