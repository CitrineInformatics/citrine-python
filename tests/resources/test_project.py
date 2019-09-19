from uuid import UUID
import pytest
from dateutil.parser import parse

from citrine.resources.project import Project, ProjectCollection
from tests.utils.factories import ProjectDataFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def project(session) -> Project:
    project = Project(
        name='Test Project',
        session=session
    )
    project.uid = UUID('16fd2706-8baf-433b-82eb-8c7fada847da')
    return project


@pytest.fixture
def collection(session) -> ProjectCollection:
    return ProjectCollection(session)


def test_string_representation(project):
    assert "<Project 'Test Project'>" == str(project)


def test_global_share_posts_content(project, session):
    project.global_share('Dataset', '2')
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method='POST',
        path='/projects/16fd2706-8baf-433b-82eb-8c7fada847da/global-share',
        json={
            'resource': {'type': 'Dataset', 'id': '2'}
        }
    )
    assert expect_call == session.last_call


def test_share_posts_content(project, session):
    project.share('1', 'MaterialTemplate', '2')

    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/projects/16fd2706-8baf-433b-82eb-8c7fada847da/share',
        json={
            'project_id': '1',
            'resource': {'type': 'MaterialTemplate', 'id': '2'}
        }
    )
    assert expected_call == session.last_call


def test_datasets_get_project_id(project):
    assert project.uid == project.datasets.project_id


def test_property_templates_get_project_id(project):
    assert project.uid == project.property_templates.project_id


def test_condition_templates_get_project_id(project):
    assert project.uid == project.condition_templates.project_id


def test_parameter_templates_get_project_id(project):
    assert project.uid == project.parameter_templates.project_id


def test_material_templates_get_project_id(project):
    assert project.uid == project.material_templates.project_id


def test_measurement_templates_get_project_id(project):
    assert project.uid == project.measurement_templates.project_id


def test_process_templates_get_project_id(project):
    assert project.uid == project.process_templates.project_id


def test_process_runs_get_project_id(project):
    assert project.uid == project.process_runs.project_id


def test_measurement_runs_get_project_id(project):
    assert project.uid == project.measurement_runs.project_id


def test_material_runs_get_project_id(project):
    assert project.uid == project.material_runs.project_id


def test_ingredient_runs_get_project_id(project):
    assert project.uid == project.ingredient_runs.project_id


def test_process_specs_get_project_id(project):
    assert project.uid == project.process_specs.project_id


def test_measurement_specs_get_project_id(project):
    assert project.uid == project.measurement_specs.project_id


def test_material_specs_get_project_id(project):
    assert project.uid == project.material_specs.project_id


def test_ingredient_specs_get_project_id(project):
    assert project.uid == project.ingredient_specs.project_id


def test_project_registration(collection, session):
    # Given
    create_time = parse('2019-09-10T00:00:00+00:00')
    project_data = ProjectDataFactory(
        name='testing',
        description='A sample project',
        created_at=int(create_time.timestamp() * 1000)  # The lib expects ms since epoch, which is really odd
    )
    session.set_response({'project': project_data})

    # When
    created_project = collection.register('testing')

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/projects',
        json={
            'name': 'testing',
            'description': None,
            'id': None,
            'status': None,
            'created_at': None,
        }
    )
    assert expected_call == session.last_call

    assert 'A sample project' == created_project.description
    assert 'CREATED' == created_project.status
    assert create_time == created_project.created_at


def test_get_project(collection, session):
    # Given
    project_data = ProjectDataFactory(name='single project')
    session.set_response({'project': project_data})

    # When
    created_project = collection.get(project_data['uid'])

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='/projects/{}'.format(project_data['uid']),
    )
    assert expected_call == session.last_call
    assert 'single project' == created_project.name


def test_list_projects(collection, session):
    # Given
    projects_data = ProjectDataFactory.create_batch(5)
    session.set_response({'projects': projects_data})

    # When
    projects = list(collection.list())

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='GET', path='/projects')
    assert expected_call == session.last_call
    assert 5 == len(projects)


def test_delete_project(collection, session):
    # Given
    uid = '151199ec-e9aa-49a1-ac8e-da722aaf74c4'

    # When
    collection.delete(uid)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='DELETE',
        path='/projects/{}'.format(uid),
    )
    assert expected_call == session.last_call
