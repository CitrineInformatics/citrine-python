"""Tests predictor collection"""
import mock
import pytest
import uuid
from copy import deepcopy

from citrine.exceptions import ModuleRegistrationFailedException, NotFound
from citrine.informatics.predictors import GraphPredictor, SimpleMLPredictor
from citrine.resources.predictor import PredictorCollection
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture(scope='module')
def basic_predictor_report_data():
    return {
        'id': str(uuid.uuid4()),
        'status': 'VALID',
        'report': {'descriptors': [], 'models': []}
    }


def test_build(valid_simple_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_simple_ml_predictor_data)
    assert predictor.name == 'ML predictor'
    assert predictor.description == 'Predicts z from input x and latent variable y'


def test_graph_build(valid_graph_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_graph_predictor_data)
    assert predictor.name == 'Graph predictor'
    assert predictor.description == 'description'
    assert len(predictor.predictors) == 2
    assert len(predictor.training_data) == 1


def test_register(valid_simple_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.post_resource.return_value = valid_simple_ml_predictor_data
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    registered = pc.register(predictor)
    assert registered.name == 'ML predictor'


def test_register_experimental(valid_simple_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    post_response = deepcopy(valid_simple_ml_predictor_data)
    post_response["experimental"] = True
    post_response["experimental_reasons"] = ["This is a test", "Of experimental reasons"]
    session.post_resource.return_value = post_response
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    with pytest.warns(UserWarning) as record:
        pc.register(predictor)
    msg = str(record[0].message)
    assert "Predictor" in msg
    assert "This is a test" in msg
    assert "Of experimental reasons" in msg


def test_graph_register(valid_graph_predictor_data, basic_predictor_report_data):
    copy_graph_data = deepcopy(valid_graph_predictor_data)
    session = mock.Mock()
    session.post_resource.return_value = copy_graph_data
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = GraphPredictor.build(valid_graph_predictor_data)
    registered = pc.register(predictor)
    assert registered.name == 'Graph predictor'


def test_failed_register(valid_simple_ml_predictor_data):
    session = mock.Mock()
    session.post_resource.side_effect = NotFound("/projects/uuid/not_found")
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    with pytest.raises(ModuleRegistrationFailedException) as e:
        pc.register(predictor)
    assert 'The "SimpleMLPredictor" failed to register. NotFound: /projects/uuid/not_found' in str(e.value)


def test_mark_predictor_invalid(valid_simple_ml_predictor_data, valid_predictor_report_data):
    # Given
    session = FakeSession()
    collection = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    session.set_responses(valid_simple_ml_predictor_data, valid_predictor_report_data)

    # When
    predictor.active = False
    collection.update(predictor)

    # Then
    assert 2 == session.num_calls, session.calls  # This is a little strange, the report is fetched eagerly

    first_call = session.calls[0]  # First call is the update
    assert first_call.method == 'PUT'
    assert first_call.path == '/projects/{}/modules/{}'.format(collection.project_id, predictor.uid)
    assert not first_call.json['active']


def test_list_predictors(valid_simple_ml_predictor_data, valid_expression_predictor_data,
                         basic_predictor_report_data):
    # Given
    session = FakeSession()
    collection = PredictorCollection(uuid.uuid4(), session)
    session.set_responses(
        {
            'entries': [valid_simple_ml_predictor_data, valid_expression_predictor_data],
            'next': ''
        },
        basic_predictor_report_data,
        basic_predictor_report_data
    )

    # When
    predictors = list(collection.list(per_page=20))

    # Then
    expected_call = FakeCall(method='GET', path='/projects/{}/modules'.format(collection.project_id),
                                   params={'per_page': 20, 'module_type': 'PREDICTOR'})
    assert 3 == session.num_calls, session.calls  # This is a little strange, the report is fetched eagerly
    assert expected_call == session.calls[0]
    assert len(predictors) == 2
