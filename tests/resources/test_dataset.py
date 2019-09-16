import unittest
from uuid import UUID

from citrine.resources.dataset import DatasetCollection
from tests.utils.factories import DatasetDataFactory, DatasetFactory
from tests.utils.session import FakeSession, FakeCall


class TestDatasetCollection(unittest.TestCase):

    def setUp(self):
        self.session = FakeSession()
        self.collection = DatasetCollection(
            project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
            session=self.session
        )

    def test_register_dataset(self):
        # Given
        name = 'Test Dataset'
        summary = 'testing summary'
        description = 'testing description'
        self.session.set_response(DatasetDataFactory(name=name, summary=summary, description=description))

        # When
        dataset = self.collection.register(DatasetFactory(name=name, summary=summary, description=description))

        self.assertEqual(1, self.session.num_calls)
        self.assertEqual(
            FakeCall(
                method='POST',
                path=f'projects/{self.collection.project_id}/datasets',
                json={'name': name, 'summary': summary, 'description': description}
            ),
            self.session.last_call,
            self.session.last_call
        )

        self.assertEqual(name, dataset.name)


class TestDataset(unittest.TestCase):
    
    def setUp(self):
        self.dataset = DatasetFactory(name='Test Dataset')
        self.dataset.project_id = UUID('6b608f78-e341-422c-8076-35adc8828545')
        self.dataset.session = None

    def test_string_representation(self):
        self.assertEqual("<Dataset 'Test Dataset'>", str(self.dataset))

    def test_property_templates_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.property_templates.project_id)

    def test_condition_templates_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.condition_templates.project_id)

    def test_parameter_templates_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.parameter_templates.project_id)

    def test_material_templates_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.material_templates.project_id)

    def test_measurement_templates_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.measurement_templates.project_id)

    def test_process_templates_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.process_templates.project_id)

    def test_process_runs_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.process_runs.project_id)

    def test_measurement_runs_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.measurement_runs.project_id)

    def test_material_runs_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.material_runs.project_id)

    def test_ingredient_runs_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.ingredient_runs.project_id)

    def test_process_specs_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.process_specs.project_id)

    def test_measurement_specs_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.measurement_specs.project_id)

    def test_material_specs_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.material_specs.project_id)

    def test_ingredient_specs_get_project_id(self):
        self.assertEqual(self.dataset.project_id, self.dataset.ingredient_specs.project_id)
