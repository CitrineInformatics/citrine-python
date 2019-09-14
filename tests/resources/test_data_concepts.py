import pytest
import unittest
import mock
import requests
from uuid import uuid4

from citrine._session import Session
from citrine.resources.measurement_spec import MeasurementSpec, MeasurementSpecCollection


class SessionTests(unittest.TestCase):
    def test_register(self):
        session = mock.Mock()
        spec_uid = str(uuid4())
        session.post_resource.return_value = {
            'uids': {'id': spec_uid},
            'name': 'spec name',
            'tags': [],
            'notes': None,
            'conditions': [],
            'parameters': [],
            'template': None,
            'file_links': [],
            'type': 'measurement_spec'
        }
        measurement_spec = MeasurementSpec("spec name", uids={'id': spec_uid})
        measurement_spec_collection = MeasurementSpecCollection(uuid4(), None, session)
        with pytest.raises(RuntimeError):
            # Cannot register if no dataset is provided
            measurement_spec_collection.register(measurement_spec)
        registered_measurement_spec = MeasurementSpec("spec name", uids={'id': spec_uid})
        assert registered_measurement_spec == measurement_spec
