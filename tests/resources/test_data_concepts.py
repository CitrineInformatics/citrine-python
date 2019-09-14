import pytest
import unittest
import mock
from uuid import uuid4

from citrine.resources.measurement_spec import MeasurementSpec, MeasurementSpecCollection
from citrine.resources.condition_template import ConditionTemplate
from taurus.entity.link_by_uid import LinkByUID
from taurus.entity.bounds.real_bounds import RealBounds

spec_uid = str(uuid4())
measurement_spec_dict = {
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

class SessionTests(unittest.TestCase):
    def test_register(self):
        """
        Mock registering an object.

        Assuming the registration returns the object in dictionary form, assert that it gets
        built into a copy of the original object.
        """
        session = mock.Mock()
        spec_uid = str(uuid4())
        session.post_resource.return_value = measurement_spec_dict
        measurement_spec = MeasurementSpec("spec name", uids={'id': measurement_spec_dict['uids']['id']})
        measurement_spec_collection = MeasurementSpecCollection(uuid4(), None, session)
        with pytest.raises(RuntimeError):
            # Cannot register if no dataset is provided
            measurement_spec_collection.register(measurement_spec)

        measurement_spec_collection = MeasurementSpecCollection(uuid4(), uuid4(), session)
        registered_measurement_spec = measurement_spec_collection.register(measurement_spec)
        assert registered_measurement_spec == measurement_spec

    def test_filter(self):
        """
        Mock the various list/filter methods.

        Assuming they all return object dictionaries in the expected form, assert that those
        dictionaries can be built into the expected objects.
        """
        session = mock.Mock()
        # mock session so that it returns a list containing the above dict after calling
        # either get_resource or post_resource.
        session.get_resource.return_value = {'contents': [measurement_spec_dict]}
        session.post_resource.return_value = {'contents': [measurement_spec_dict]}
        measurement_spec = MeasurementSpec("spec name", uids={'id': measurement_spec_dict['uids']['id']})
        measurement_spec_collection = MeasurementSpecCollection(uuid4(), uuid4(), session)

        # List
        list_response = measurement_spec_collection.list()
        assert next(iter(list_response)) == measurement_spec

        # Filter by tags
        filter_by_tags_response = measurement_spec_collection.filter_by_tags(['tag 1', 'tag 2'])
        assert next(iter(filter_by_tags_response)) == measurement_spec

        # Filter by name
        filter_by_name_response = measurement_spec_collection.filter_by_name('some name', True)
        assert next(iter(filter_by_name_response)) == measurement_spec

        # Filter by attribute, using either an attribute template or a LinkByUID
        cond_template = ConditionTemplate("a template", bounds=RealBounds(0, 1000, ''))
        cond_template_link = LinkByUID(scope='id', id=uuid4())
        bounds = RealBounds(0, 100, '')
        filter_by_attribute_bounds_response = \
            measurement_spec_collection.filter_by_attribute_bounds({cond_template: bounds})
        assert next(iter(filter_by_attribute_bounds_response)) == measurement_spec
        filter_by_attribute_bounds_response = \
            measurement_spec_collection.filter_by_attribute_bounds({cond_template_link: bounds})
        assert next(iter(filter_by_attribute_bounds_response)) == measurement_spec

        # Trying to filter by name without a dataset id throws an error
        measurement_spec_collection = MeasurementSpecCollection(uuid4(), None, session)
        with pytest.raises(RuntimeError):
            measurement_spec_collection.filter_by_name("some name", True)
