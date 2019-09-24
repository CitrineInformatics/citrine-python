"""Tests predictor collection"""
import mock
import uuid

from citrine.informatics.predictors import ParaboloidPredictor
from citrine.resources.predictor import PredictorCollection
from ..serialization.test_predictors import valid_paraboloid_data, valid_simple_ml_data


def test_build(valid_paraboloid_data):
    pc = PredictorCollection(uuid.uuid4(), mock.Mock())
    predictor = pc.build(valid_paraboloid_data)
    assert predictor.name == 'my predictor'
    assert predictor.description == 'does some things'


def test_register(valid_paraboloid_data):
    session = mock.Mock()
    session.post_resource.return_value = valid_paraboloid_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = ParaboloidPredictor.build(valid_paraboloid_data)
    registered = pc.register(predictor)
    assert registered.name == 'my predictor'
