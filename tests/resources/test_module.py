"""Tests predictor collection"""
import mock
import uuid

from citrine.resources.module import ModuleCollection
from citrine.informatics.predictors import SimpleMLPredictor


def test_build(valid_simple_ml_predictor_data):
    session = mock.Mock()
    session.get_resource.return_value = {
        'id': str(uuid.uuid4()),
        'status': 'VALID',
        'report': {}
    }
    collection = ModuleCollection(uuid.uuid4(), session)
    module = collection.build(valid_simple_ml_predictor_data)
    assert type(module) == SimpleMLPredictor
