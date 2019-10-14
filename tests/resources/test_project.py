import uuid
import pytest
from dateutil.parser import parse

from citrine.resources.project import Project, ProjectCollection
from citrine.resources.table import TableCollection
from tests.utils.factories import ProjectDataFactory, UserDataFactory
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
    project.uid = uuid.UUID('16fd2706-8baf-433b-82eb-8c7fada847da')
    return project


@pytest.fixture
def collection(session) -> ProjectCollection:
    return ProjectCollection(session)


def test_string_representation(project):
    assert "<Project 'Test Project'>" == str(project)


def test_share_post_content(project, session):
    # Given
    dataset_id = str(uuid.uuid4())

    # When
    project.share(project.uid, 'DATASET', dataset_id)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/projects/{}/share'.format(project.uid),
        json={
            'project_id': project.uid,
            'resource': {'type': 'DATASET', 'id': dataset_id}
        }
    )
    assert expected_call == session.last_call


def test_make_resource_public_post_content(project, session):
    dataset_id = str(uuid.uuid4())
    dataset = project.datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))
    assert project.make_public(dataset)

    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/projects/{}/make-public'.format(project.uid),
        json={
            'resource': {'type': 'DATASET', 'id': dataset_id}
        }
    )
    assert expected_call == session.last_call


def test_make_resource_private_post_content(project, session):
    dataset_id = str(uuid.uuid4())
    dataset = project.datasets.build(dict(
        id=dataset_id,
        name="private dataset", summary="test", description="test"
    ))
    assert project.make_private(dataset)
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/projects/{}/make-private'.format(project.uid),
        json={
            'resource': {'type': 'DATASET', 'id': dataset_id}
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


def test_design_spaces_get_project_id(project):
    assert project.uid == project.design_spaces.project_id


def test_processors_get_project_id(project):
    assert project.uid == project.processors.project_id


def test_predictors_get_project_id(project):
    assert project.uid == project.predictors.project_id


def test_workflows_get_project_id(project):
    assert project.uid == project.workflows.project_id


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
    created_project = collection.get(project_data['id'])

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='GET',
        path='/projects/{}'.format(project_data['id']),
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


def test_list_projects_with_page_params(collection, session):
    # Given
    project_data = ProjectDataFactory()
    session.set_response({'projects': [project_data]})

    # When
    list(collection.list(page=3, per_page=10))

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='GET', path='/projects', params={'page': 3, 'per_page': 10})
    assert expected_call == session.last_call


def test_delete_project(collection, session):
    # Given
    uid = '151199ec-e9aa-49a1-ac8e-da722aaf74c4'

    # When
    with pytest.raises(NotImplementedError):
        collection.delete(uid)


def test_list_members(project, session):
    # Given
    user = UserDataFactory()
    session.set_response({'users': [user]})

    # When
    project.list_members()

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method='GET', path='/projects/{}/users'.format(project.uid))
    assert expect_call == session.last_call


def test_set_member(project, session):
    # Given
    user = UserDataFactory()
    session.set_response({'actions': ["READ", "INVITE"], 'role': 'MEMBER'})

    # When
    project.set_member(user["id"], 'MEMBER', ["READ", "INVITE"])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method="POST", path='/projects/{}/users/{}'.format(project.uid, user["id"]), json={
        "role": "MEMBER",
        "actions": ["READ", "INVITE"]
    })
    assert expect_call == session.last_call


def test_remove_member(project, session):
    # Given
    user = UserDataFactory()

    # When
    project.remove_member(user["id"])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="DELETE",
        path="/projects/{}/users/{}".format(project.uid, user["id"])
    )
    assert expect_call == session.last_call


def test_project_tables(project):
    assert isinstance(project.tables, TableCollection)
