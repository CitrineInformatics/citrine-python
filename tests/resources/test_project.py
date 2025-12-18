import json
import uuid
from unittest import mock

import pytest
from dateutil.parser import parse
from gemd.entity.link_by_uid import LinkByUID

from citrine.exceptions import NotFound, ModuleRegistrationFailedException
from citrine.informatics.predictors import GraphPredictor
from citrine.resources.api_error import ApiError, ValidationError
from citrine.resources.dataset import Dataset, DatasetCollection
from citrine.resources.gemtables import GemTableCollection
from citrine.resources.process_spec import ProcessSpec
from citrine.resources.project import Project, ProjectCollection
from citrine.resources.project_member import ProjectMember
from citrine.resources.project_roles import MEMBER, LEAD, WRITE
from tests.utils.factories import ProjectDataFactory, UserDataFactory, TeamDataFactory
from tests.utils.session import FakeSession, FakeCall, FakePaginatedSession, FakeRequestResponse
from citrine.resources.team import  READ, TeamMember


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def paginated_session() -> FakePaginatedSession:
    return FakePaginatedSession()


@pytest.fixture
def paginated_collection(paginated_session) -> ProjectCollection:
    return ProjectCollection(
        session=paginated_session
    )


@pytest.fixture
def project(session) -> Project:
    project = Project(
        name='Test Project',
        session=session,
        team_id=uuid.UUID('11111111-8baf-433b-82eb-8c7fada847da')
    )
    project.uid = uuid.UUID('16fd2706-8baf-433b-82eb-8c7fada847da')
    return project


@pytest.fixture
def collection(session) -> ProjectCollection:
    return ProjectCollection(session, team_id=uuid.uuid4())


def test_get_team_id_from_project(session):
    team_id = uuid.UUID('6b608f78-e341-422c-8076-35adc8828000')
    check_project = {'project': {'team': {'id': team_id}}}
    session.set_response(check_project)
    p = Project(name='Test Project', session=session)
    assert p.team_id == team_id


def test_string_representation(project):
    assert "<Project 'Test Project'>" == str(project)


def test_publish_resource(project, session):
    predictor = GraphPredictor(name="foo", description="foo", predictors=[])
    predictor.uid = uuid.uuid4()
    assert project.publish(resource=predictor)

    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'/projects/{project.uid}/published-resources/MODULE/batch-publish',
        json={
            'ids': [str(predictor.uid)]
        }
    )
    assert expected_call == session.last_call


def test_publish_resource_dataset(project, session):
    dataset = Dataset("public dataset", summary="test", description="test")
    with pytest.raises(ValueError):
        assert project.publish(resource=dataset)


def test_pull_in_resource(project, session):
    predictor = GraphPredictor(name="foo", description="foo", predictors=[])
    predictor.uid = uuid.uuid4()
    assert project.pull_in_resource(resource=predictor)

    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'/teams/{project.team_id}/projects/{project.uid}/outside-resources/MODULE/batch-pull-in',
        json={
            'ids': [str(predictor.uid)]
        }
    )
    assert expected_call == session.last_call


def test_pull_in_resource_dataset(project, session):
    dataset = Dataset("public dataset", summary="test", description="test")
    with pytest.raises(ValueError):
        assert project.pull_in_resource(resource=dataset)


def test_un_publish_resource(project, session):
    predictor = GraphPredictor(name="foo", description="foo", predictors=[])
    predictor.uid = uuid.uuid4()
    assert project.un_publish(resource=predictor)

    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'/projects/{project.uid}/published-resources/MODULE/batch-un-publish',
        json={
            'ids': [str(predictor.uid)]
        }
    )
    assert expected_call == session.last_call


def test_un_publish_resource_dataset(project, session):
    dataset = Dataset("public dataset", summary="test", description="test")
    with pytest.raises(ValueError):
        assert project.un_publish(resource=dataset)


def test_design_spaces_get_project_id(project):
    assert project.uid == project.design_spaces.project_id


def test_descriptors_get_project_id(project):
    assert project.uid == project.descriptors.project_id


def test_predictors_get_project_id(project):
    assert project.uid == project.predictors.project_id


def test_predictor_evaluations_get_project_id(project):
    assert project.uid == project.predictor_evaluations.project_id


def test_design_workflows_get_project_id(project):
    assert project.uid == project.design_workflows.project_id


def test_design_workflows_get_branch(project):
    assert None is project.design_workflows.branch_root_id
    assert None is project.design_workflows.branch_version


def test_generative_design_executions_get_project_id(project):
    assert project.uid == project.generative_design_executions.project_id


def test_branches_get_project_id(project):
    assert project.uid == project.branches.project_id


def test_ara_definitions_get_project_id(project):
    assert project.uid == project.table_configs.project_id


def test_failed_register():
    team_id = uuid.uuid4()
    session = mock.Mock()
    session.post_resource.side_effect = NotFound(f'/teams/{team_id}/projects',
                                                 FakeRequestResponse(400))
    project_collection = ProjectCollection(session=session, team_id=team_id)
    with pytest.raises(ModuleRegistrationFailedException) as e:
        project_collection.register("Project")
    assert 'The "Project" failed to register.' in str(e.value)
    assert f'/teams/{team_id}/projects' in str(e.value)


def test_failed_register_no_team(session):
    project_collection = ProjectCollection(session=session)
    with pytest.raises(NotImplementedError):
        project_collection.register("Project")


def test_project_registration(collection: ProjectCollection, session):
    # Given
    create_time = parse('2019-09-10T00:00:00+00:00')
    project_data = ProjectDataFactory(
        name='testing',
        description='A sample project',
        created_at=int(create_time.timestamp() * 1000)  # The lib expects ms since epoch, which is really odd
    )
    session.set_response({'project': project_data})
    team_id = collection.team_id

    # When
    created_project = collection.register('testing')

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'teams/{team_id}/projects',
        json={
            'name': 'testing'
        }
    )
    assert expected_call == session.last_call

    assert 'A sample project' == created_project.description
    assert 'CREATED' == created_project.status
    assert create_time == created_project.created_at


def test_get_project(collection: ProjectCollection, session):
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
    expected_call = FakeCall(method='GET',
                             path=f'/teams/{collection.team_id}/projects',
                             params={'per_page': 1000, 'page': 1},
                             version="v3")
    assert expected_call == session.last_call
    assert 5 == len(projects)


def test_list_archived_projects(collection, session):
    # Given
    projects_data = ProjectDataFactory.create_batch(5)
    session.set_response({'projects': projects_data})

    # When
    projects = list(collection.list_archived())

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='GET',
                             path=f'/teams/{collection.team_id}/projects',
                             params={'per_page': 1000, 'page': 1, 'archived': "true"},
                             version="v3")
    assert expected_call == session.last_call
    assert 5 == len(projects)


def test_list_active_projects(collection, session):
    # Given
    projects_data = ProjectDataFactory.create_batch(5)
    session.set_response({'projects': projects_data})

    # When
    projects = list(collection.list_active())

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='GET',
                             path=f'/teams/{collection.team_id}/projects',
                             params={'per_page': 1000, 'page': 1, 'archived': "false"},
                             version="v3")
    assert expected_call == session.last_call
    assert 5 == len(projects)


def test_list_no_team(session):
    project_collection = ProjectCollection(session=session)
    projects_data = ProjectDataFactory.create_batch(5)
    session.set_response({'projects': projects_data})

    projects = list(project_collection.list())

    assert 1 == session.num_calls
    expected_call = FakeCall(method='GET', path='/projects', params={'per_page': 1000, 'page': 1})
    assert expected_call == session.last_call
    assert 5 == len(projects)


def test_list_projects_with_page_params(collection, session):
    # Given
    project_data = ProjectDataFactory()
    session.set_response({'projects': [project_data]})

    # When
    list(collection.list(per_page=10))

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='GET', path=f'/teams/{collection.team_id}/projects', params={'per_page': 10, 'page': 1})
    assert expected_call == session.last_call

def test_search_all_no_team(session):
    project_collection = ProjectCollection(session=session)
    projects_data = ProjectDataFactory.create_batch(2)
    project_name_to_match = projects_data[0]['name']

    search_params = {
        'name': {
            'value': project_name_to_match,
            'search_method': 'EXACT'}}
    expected_response = [p for p in projects_data if p["name"] == project_name_to_match]

    project_collection.session.set_response({'projects': expected_response})

    # Then
    results = list(project_collection.search_all(search_params=search_params))

    expected_call = FakeCall(method='POST', path='/projects/search', params={'userId': ''}, json={'search_params': search_params})

    assert 1 == project_collection.session.num_calls
    assert expected_call == project_collection.session.last_call
    assert 1 == len(results)

def test_search_all(collection: ProjectCollection):
    # Given
    projects_data = ProjectDataFactory.create_batch(2)
    project_name_to_match = projects_data[0]['name']

    search_params = {
        'name': {
            'value': project_name_to_match,
            'search_method': 'EXACT'}}
    expected_response = [p for p in projects_data if p["name"] == project_name_to_match]

    collection.session.set_response({'projects': expected_response})

    # Then
    results = list(collection.search_all(search_params=search_params))

    expected_call = FakeCall(method='POST',
                             path=f'/teams/{collection.team_id}/projects/search',
                             params={'userId': ''},
                             json={'search_params': {
                                 'name': {
                                     'value': project_name_to_match,
                                     'search_method': 'EXACT'}}})

    assert 1 == collection.session.num_calls
    assert expected_call == collection.session.last_call
    assert 1 == len(results)

def test_search_all_no_search_params(collection: ProjectCollection):
    # Given
    projects_data = ProjectDataFactory.create_batch(2)

    expected_response = projects_data

    collection.session.set_response({'projects': expected_response})

    # Then
    result = list(collection.search_all(search_params=None))

    expected_call = FakeCall(method='POST',
                             path=f'/teams/{collection.team_id}/projects/search',
                             params={'userId': ''},
                             json={})

    assert 1 == collection.session.num_calls
    assert expected_call == collection.session.last_call
    assert len(expected_response) == len(result)


def test_search_projects(collection: ProjectCollection):
    # Given
    projects_data = ProjectDataFactory.create_batch(2)
    project_name_to_match = projects_data[0]['name']

    search_params = {
        'name': {
            'value': project_name_to_match,
            'search_method': 'EXACT'}}
    expected_response = [p for p in projects_data if p["name"] == project_name_to_match]

    collection.session.set_response({'projects': expected_response})

    # Then
    result = list(collection.search(search_params=search_params))

    expected_call = FakeCall(method='POST',
                             path=f'/teams/{collection.team_id}/projects/search',
                             params={'userId': ''},
                             json={'search_params': {
                                 'name': {
                                     'value': project_name_to_match,
                                     'search_method': 'EXACT'}}})

    assert 1 == collection.session.num_calls
    assert expected_call == collection.session.last_call
    assert 1 == len(result)

def test_search_projects_no_search_params(collection: ProjectCollection):
    # Given
    projects_data = ProjectDataFactory.create_batch(2)

    expected_response = projects_data

    collection.session.set_response({'projects': expected_response})

    # Then
    result = list(collection.search())

    expected_call = FakeCall(method='POST', path=f'/teams/{collection.team_id}/projects/search', params={'userId': ''}, json={})

    assert 1 == collection.session.num_calls
    assert expected_call == collection.session.last_call
    assert len(projects_data) == len(result)


def test_archive_project(collection, session):
    # Given
    uid = '151199ec-e9aa-49a1-ac8e-da722aaf74c4'

    # When
    collection.archive(uid)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='POST', path=f'/projects/{uid}/archive')
    assert expected_call == session.last_call


def test_restore_project(collection, session):
    # Given
    uid = '151199ec-e9aa-49a1-ac8e-da722aaf74c4'

    # When
    collection.restore(uid)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='POST', path=f'/projects/{uid}/restore')
    assert expected_call == session.last_call


def test_delete_project(collection, session):
    # Given
    uid = '151199ec-e9aa-49a1-ac8e-da722aaf74c4'

    # When
    collection.delete(uid)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='DELETE', path=f'/projects/{uid}')
    assert expected_call == session.last_call


def test_update_project(collection: ProjectCollection, project):
    project.name = "updated name"
    with pytest.raises(NotImplementedError):
        collection.update(project)


def test_list_members(project, session):
    # Given
    user = UserDataFactory()
    user["actions"] = READ
    user.pop("position")

    team_data = TeamDataFactory(
        id=str(project.team_id),
    )

    session.set_responses(
        {'team': team_data},
        {'users': [user]}
    )

    # When
    members = project.list_members()

    # Then
    assert 2 == session.num_calls
    expect_call_1 = FakeCall(method='GET', path=f'/teams/{team_data["id"]}')
    expect_call_2 = FakeCall(method='GET', path=f'/teams/{project.team_id}/users')
    assert expect_call_1 == session.calls[0]
    assert expect_call_2 == session.calls[1]
    assert isinstance(members[0], TeamMember)


def test_project_tables(project):
    assert isinstance(project.tables, GemTableCollection)
