"""Tests predictor collection"""
import mock
import pytest
import uuid

from citrine.exceptions import ModuleRegistrationFailedException, NotFound
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


def test_failed_register(valid_paraboloid_data):
    session = mock.Mock()
    session.post_resource.side_effect = NotFound("/projects/uuid/not_found")
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = ParaboloidPredictor.build(valid_paraboloid_data)
    with pytest.raises(ModuleRegistrationFailedException) as e:
        pc.register(predictor)
    assert 'The "ParaboloidPredictor" failed to register. NotFound: /projects/uuid/not_found' in str(e.value)
