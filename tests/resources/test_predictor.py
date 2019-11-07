"""Tests predictor collection"""
import mock
import pytest
import uuid

from citrine.exceptions import ModuleRegistrationFailedException, NotFound
from citrine.informatics.predictors import SimpleMLPredictor
from citrine.resources.predictor import PredictorCollection


def test_build(valid_simple_ml_predictor_data):
    session = mock.Mock()
    session.get_resource.return_value = {
        'id': str(uuid.uuid4()),
        'status': 'VALID',
        'report': {}
    }
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_simple_ml_predictor_data)
    assert predictor.name == 'ML predictor'
    assert predictor.description == 'Predicts z from input x and latent variable y'


def test_register(valid_simple_ml_predictor_data):
    session = mock.Mock()
    session.post_resource.return_value = valid_simple_ml_predictor_data
    session.get_resource.return_value = {
        'id': str(uuid.uuid4()),
        'status': 'VALID',
        'report': {}
    }
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    registered = pc.register(predictor)
    assert registered.name == 'ML predictor'


def test_failed_register(valid_simple_ml_predictor_data):
    session = mock.Mock()
    session.post_resource.side_effect = NotFound("/projects/uuid/not_found")
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    with pytest.raises(ModuleRegistrationFailedException) as e:
        pc.register(predictor)
    assert 'The "SimpleMLPredictor" failed to register. NotFound: /projects/uuid/not_found' in str(e.value)
