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
