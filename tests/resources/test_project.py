import unittest
from dateutil.parser import parse

from citrine.resources.project import Project, ProjectCollection
from tests.utils.factories import ProjectDataFactory
from ..utils.session import FakeCall, FakeSession


class TestProject(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.session = FakeSession()
        self.project = Project(
            name='Test Project',
            session=self.session
        )
        self.project.uid = '16fd2706-8baf-433b-82eb-8c7fada847da'

    def test_string_representation(self):
        self.assertEqual("<Project 'Test Project'>", str(self.project))

    def test_share_posts_content(self):
        self.project.share('1', 'MaterialTemplate', '2')

        self.assertEqual(1, self.session.num_calls)
        self.assertEqual(
            FakeCall('POST', '/projects/16fd2706-8baf-433b-82eb-8c7fada847da/share', {
                'project_id': '1',
                'resource': {'type': 'MaterialTemplate', 'id': '2'}
            }),
            self.session.last_call,
        )

    def test_datasets_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.datasets.project_id)

    def test_property_templates_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.property_templates.project_id)

    def test_condition_templates_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.condition_templates.project_id)

    def test_parameter_templates_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.parameter_templates.project_id)

    def test_material_templates_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.material_templates.project_id)

    def test_measurement_templates_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.measurement_templates.project_id)

    def test_process_templates_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.process_templates.project_id)

    def test_process_runs_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.process_runs.project_id)

    def test_measurement_runs_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.measurement_runs.project_id)

    def test_material_runs_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.material_runs.project_id)

    def test_ingredient_runs_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.ingredient_runs.project_id)

    def test_process_specs_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.process_specs.project_id)

    def test_measurement_specs_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.measurement_specs.project_id)

    def test_material_specs_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.material_specs.project_id)

    def test_ingredient_specs_get_project_id(self):
        self.assertEqual(self.project.uid, self.project.ingredient_specs.project_id)


class TestProjectCollection(unittest.TestCase):

    def setUp(self):
        self.session = FakeSession()
        self.collection = ProjectCollection(self.session)

    def test_project_registration(self):
        # Given
        create_time = parse('2019-09-10T00:00:00+00:00')
        project_data = ProjectDataFactory(
            name='testing',
            description='A sample project',
            created_at=int(create_time.timestamp() * 1000)  # The lib expects ms since epoch, which is really odd
        )
        self.session.set_response({'project': project_data})

        # When
        created_project = self.collection.register('testing')

        # Then
        self.assertEqual(1, self.session.num_calls)
        self.assertEqual(
            FakeCall('POST', '/projects', {
                'name': 'testing',
                'description': None,
                'id': None,
                'status': None,
                'created_at': None,
            }),
            self.session.last_call,
        )

        self.assertEqual('A sample project', created_project.description)
        self.assertEqual('CREATED', created_project.status)
        self.assertEqual(create_time, created_project.created_at)
