"""Tests predictor collection"""
import mock
import pytest
import uuid

from citrine.exceptions import ModuleRegistrationFailedException, NotFound
from citrine.informatics.predictors import SimpleMLPredictor
from citrine.resources.predictor import PredictorCollection
from tests.utils.session import FakeSession, FakeCall
from ..serialization.test_predictors import valid_simple_ml_data


def test_build(valid_simple_ml_data):
    session = mock.Mock()
    session.get_resource.return_value = {
        'id': str(uuid.uuid4()),
        'status': 'VALID',
        'report': {}
    }
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_simple_ml_data)
    assert predictor.name == 'ML predictor'
    assert predictor.description == 'Predicts z from input x and latent variable y'


def test_register(valid_simple_ml_data):
    session = mock.Mock()
    session.post_resource.return_value = valid_simple_ml_data
    session.get_resource.return_value = {
        'id': str(uuid.uuid4()),
        'status': 'VALID',
        'report': {}
    }
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_data)
    registered = pc.register(predictor)
    assert registered.name == 'ML predictor'


def test_failed_register(valid_simple_ml_data):
    session = mock.Mock()
    session.post_resource.side_effect = NotFound("/projects/uuid/not_found")
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_data)
    with pytest.raises(ModuleRegistrationFailedException) as e:
        pc.register(predictor)
    assert 'The "SimpleMLPredictor" failed to register. NotFound: /projects/uuid/not_found' in str(e.value)


def test_mark_predictor_invalid(valid_simple_ml_data):
    # Given
    session = FakeSession()
    collection = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_data)
    session.set_response(valid_simple_ml_data)

    # When
    predictor.active = False
    collection.update(predictor)

    # Then
    assert 2 == session.num_calls, session.calls  # This is a little strange, the report is fetched eagerly

    first_call = session.calls[0]  # First call is the update
    assert first_call.method == 'PUT'
    assert first_call.path == '/projects/{}/modules/{}'.format(collection.project_id, predictor.uid)
    assert not first_call.json['active']
