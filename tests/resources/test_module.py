"""Tests predictor collection"""
import mock
import uuid

from citrine.resources.module import ModuleCollection
from citrine.informatics.design_spaces import ProductDesignSpace


def test_build(valid_product_design_space_data):
    session = mock.Mock()
    session.get_resource.return_value = {
        'id': str(uuid.uuid4()),
        'status': 'VALID',
        'report': {}
    }
    collection = ModuleCollection(uuid.uuid4(), session)
    module = collection.build(valid_product_design_space_data)
    assert type(module) == ProductDesignSpace
