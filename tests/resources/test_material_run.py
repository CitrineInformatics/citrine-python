import unittest
from uuid import UUID

from taurus.entity.bounds.integer_bounds import IntegerBounds

from citrine.resources.material_run import MaterialRunCollection
from tests.utils.session import FakeSession, FakeCall
from tests.utils.factories import MaterialRunFactory, MaterialRunDataFactory, LinkByUIDFactory


class TestMaterialRunCollection(unittest.TestCase):

    def setUp(self):
        self.session = FakeSession()
        self.collection = MaterialRunCollection(
            project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
            dataset_id=UUID('8da51e93-8b55-4dd3-8489-af8f65d4ad9a'),
            session=self.session
        )

    def test_register_material_run(self):
        # Given
        self.session.set_response(MaterialRunDataFactory(name='Test MR 123'))
        material_run = MaterialRunFactory()

        # When
        registered = self.collection.register(material_run)

        # Then
        self.assertEqual("<Material run 'Test MR 123'>", str(registered))

    def test_get_history(self):
        # Given
        self.session.set_response({
            'context': 'Ignored',
            'root': MaterialRunDataFactory(name='Historic MR')
        })

        # When
        run = self.collection.get_history('id', '1234')

        # Then
        self.assertEqual(1, self.session.num_calls)
        self.assertEqual(
            FakeCall('GET', f'projects/{self.collection.project_id}/material-history/id/1234'),
            self.session.last_call
        )
        self.assertEqual('Historic MR', run.name)

    def test_get_material_run(self):
        # Given
        run_data = MaterialRunDataFactory(name='Cake 2')
        mr_id = run_data['uids']['id']
        self.session.set_response(run_data)

        # When
        run = self.collection.get(mr_id)

        # Then
        self.assertEqual(1, self.session.num_calls)
        self.assertEqual(
            FakeCall('GET', f'projects/{self.collection.project_id}/datasets/{self.collection.dataset_id}/material-runs/id/{mr_id}'),
            self.session.last_call
        )
        self.assertEqual('Cake 2', run.name)

    def test_list_material_runs(self):
        # Given
        sample_run = MaterialRunDataFactory()
        self.session.set_response({
            'contents': [sample_run]
        })

        # When
        runs = self.collection.list()

        # Then
        self.assertEqual(1, self.session.num_calls)
        self.assertEqual(
            FakeCall(
                method='GET',
                path=f'projects/{self.collection.project_id}/material-runs',
                params={
                    'dataset_id': str(self.collection.dataset_id),
                    'tags': []
                }
            ),
            self.session.last_call
        )

        self.assertEqual(1, len(runs))
        self.assertEqual(sample_run['uids'], runs[0].uids)

    def test_filter_by_name(self):
        # Given
        sample_run = MaterialRunDataFactory()
        self.session.set_response({
            'contents': [sample_run]
        })

        # When
        runs = self.collection.filter_by_name('test run')

        # Then
        self.assertEqual(1, self.session.num_calls)
        self.assertEqual(
            FakeCall(
                method='GET',
                path=f'projects/{self.collection.project_id}/material-runs/filter-by-name',
                params={
                    'dataset_id': str(self.collection.dataset_id),
                    'name': 'test run',
                    'exact': False
                }
            ),
            self.session.last_call
        )

        self.assertEqual(1, len(runs))
        self.assertEqual(sample_run['uids'], runs[0].uids)

    def test_filter_by_attribute_bounds(self):
        # Given
        sample_run = MaterialRunDataFactory()
        self.session.set_response({
            'contents': [sample_run]
        })
        link = LinkByUIDFactory()
        bounds = { link: IntegerBounds(1, 5) }

        # When
        runs = self.collection.filter_by_attribute_bounds(bounds)

        # Then
        self.assertEqual(1, self.session.num_calls)
        self.assertEqual(
            FakeCall(
                method='POST',
                path=f'projects/{self.collection.project_id}/material-runs/filter-by-attribute-bounds',
                json={'attribute_bounds': {link.id: {'lower_bound': 1, 'upper_bound': 5, 'type': 'integer_bounds'}}}
            ),
            self.session.last_call
        )

        self.assertEqual(1, len(runs))
        self.assertEqual(sample_run['uids'], runs[0].uids)
