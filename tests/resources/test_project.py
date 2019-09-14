import pytest
import unittest
import mock
import requests
from uuid import uuid4

from citrine._session import Session
from citrine.resources.project import Project, ProjectCollection

project_dict = {
    'id': str(uuid4()),
    'created_at': 1559933807392,
    'name': 'my project',
    'description': 'a good project',
    'status': 'in-progress'
}

class SessionTests(unittest.TestCase):
    def test_build_project(self):
        """
        Build a project from a dictionary using both the Resource and Collection methods.

        The results should be identical.
        """
        session = mock.Mock()
        project = Project.build(project_dict)
        project.session = session

        project_collection = ProjectCollection(session)
        built_project = project_collection.build(project_dict)
        assert built_project.dump() == project.dump()

    def test_register(self):
        """
        Register a project a project collection.

        Check that the resulting dictionary is a copy of the original project.
        """
        session = mock.Mock()
        project_collection = ProjectCollection(session)
        session.post_resource.return_value = {'project': project_dict}
        built_project = project_collection.register('my project', 'a good project')
        assert built_project.dump() == project_dict

    def test_list(self):
        """
        List the projects in a collection

        Check that the resulting dictionary is a copy of the original project.
        """
        session = mock.Mock()
        project_collection = ProjectCollection(session)
        session.get_resource.return_value = {'projects': [project_dict]}
        projects_iterator = project_collection.list()
        assert next(projects_iterator).dump() == project_dict

    def test_project_has_collections(self):
        """Check that a project has all expected collections."""
        session = mock.Mock()
        project = Project.build(project_dict)
        project.session = session
        assert project.datasets.project_id == project.uid
        assert project.property_templates.project_id == project.uid
        assert project.condition_templates.project_id == project.uid
        assert project.parameter_templates.project_id == project.uid
        assert project.material_templates.project_id == project.uid
        assert project.process_templates.project_id == project.uid
        assert project.measurement_templates.project_id == project.uid
        assert project.process_runs.project_id == project.uid
        assert project.process_specs.project_id == project.uid
        assert project.material_runs.project_id == project.uid
        assert project.material_specs.project_id == project.uid
        assert project.measurement_runs.project_id == project.uid
        assert project.measurement_specs.project_id == project.uid
        assert project.ingredient_runs.project_id == project.uid
        assert project.ingredient_specs.project_id == project.uid
