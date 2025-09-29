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


@pytest.fixture
def datasets(project) -> DatasetCollection:
    with pytest.deprecated_call():
        return project.datasets


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


def test_publish_resource_deprecated(project, datasets, session):
    dataset_id = str(uuid.uuid4())
    dataset = datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))
    with pytest.deprecated_call():
        assert project.publish(resource=dataset)

    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'/projects/{project.uid}/published-resources/DATASET/batch-publish',
        json={
            'ids': [str(dataset.uid)]
        }
    )
    assert expected_call == session.last_call


def test_pull_in_resource(project, datasets, session):
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


def test_pull_in_resource_deprecated(project, datasets, session):
    dataset_id = str(uuid.uuid4())
    dataset = datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))
    with pytest.deprecated_call():
        assert project.pull_in_resource(resource=dataset)

    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'/teams/{project.team_id}/projects/{project.uid}/outside-resources/DATASET/batch-pull-in',
        json={
            'ids': [str(dataset.uid)]
        }
    )
    assert expected_call == session.last_call


def test_un_publish_resource(project, datasets, session):
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


def test_un_publish_resource_deprecated(project, datasets, session):
    dataset_id = str(uuid.uuid4())
    dataset = datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))
    with pytest.deprecated_call():
        assert project.un_publish(resource=dataset)

    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'/projects/{project.uid}/published-resources/DATASET/batch-un-publish',
        json={
            'ids': [str(dataset.uid)]
        }
    )
    assert expected_call == session.last_call


def test_datasets_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.datasets

    assert project.uid == collection.project_id


def test_property_templates_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.property_templates
    
    assert project.uid == collection.project_id


def test_condition_templates_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.condition_templates

    assert project.uid == collection.project_id


def test_parameter_templates_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.parameter_templates

    assert project.uid == collection.project_id


def test_material_templates_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.material_templates

    assert project.uid == collection.project_id


def test_measurement_templates_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.measurement_templates

    assert project.uid == collection.project_id


def test_process_templates_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.process_templates

    assert project.uid == collection.project_id


def test_process_runs_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.process_runs

    assert project.uid == collection.project_id


def test_measurement_runs_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.measurement_runs

    assert project.uid == collection.project_id


def test_material_runs_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.material_runs

    assert project.uid == collection.project_id


def test_ingredient_runs_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.ingredient_runs

    assert project.uid == collection.project_id


def test_process_specs_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.process_specs

    assert project.uid == collection.project_id


def test_measurement_specs_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.measurement_specs

    assert project.uid == collection.project_id


def test_material_specs_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.material_specs

    assert project.uid == collection.project_id


def test_ingredient_specs_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.ingredient_specs

    assert project.uid == collection.project_id


def test_gemd_resource_get_project_id(project):
    with pytest.deprecated_call():
        collection = project.gemd

    assert project.uid == collection.project_id


def test_design_spaces_get_project_id(project):
    assert project.uid == project.design_spaces.project_id


def test_descriptors_get_project_id(project):
    assert project.uid == project.descriptors.project_id


def test_predictors_get_project_id(project):
    assert project.uid == project.predictors.project_id


def test_pe_workflows_get_project_id(project):
    with pytest.deprecated_call():
        assert project.uid == project.predictor_evaluation_workflows.project_id


def test_pe_executions_get_project_id(project):
    with pytest.deprecated_call():
        assert project.uid == project.predictor_evaluation_executions.project_id
    # The resulting collection cannot be used to trigger executions.
    with pytest.deprecated_call():
        with pytest.raises(RuntimeError):
            project.predictor_evaluation_executions.trigger(uuid.uuid4())


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


def test_project_batch_delete_no_errors(project, session):
    job_resp = {
        'job_id': '1234'
    }

    # Actual response-like data - note there is no 'failures' array within 'output'
    successful_job_resp = {
        'job_type': 'batch_delete',
        'status': 'Success',
        'tasks': [
            {
                "id": "7b6bafd9-f32a-4567-b54c-7ce594edc018", "task_type": "batch_delete",
                "status": "Success", "dependencies": []
             }
            ],
        'output': {}
    }

    session.set_responses(job_resp, successful_job_resp)

    # When
    with pytest.deprecated_call():
        del_resp = project.gemd_batch_delete([uuid.UUID('16fd2706-8baf-433b-82eb-8c7fada847da')])

    # Then
    assert len(del_resp) == 0

    # When trying with entities
    session.set_responses(job_resp, successful_job_resp)
    entity = ProcessSpec(name="proc spec", uids={'id': '16fd2706-8baf-433b-82eb-8c7fada847da'})
    with pytest.deprecated_call():
        del_resp = project.gemd_batch_delete([entity])

    # Then
    assert len(del_resp) == 0


def test_project_batch_delete(project, session):
    job_resp = {
        'job_id': '1234'
    }

    failures_escaped_json = json.dumps([
        {
            "id": {
                'scope': 'somescope',
                'id': 'abcd-1234'
            },
            'cause': {
                "code": 400,
                "message": "",
                "validation_errors": [
                    {
                        "failure_message": "fail msg",
                        "failure_id": "identifier.coreid.missing"
                    }
                ]
            }
        }
    ])

    failed_job_resp = {
        'job_type': 'batch_delete',
        'status': 'Success',
        'tasks': [],
        'output': {
            'failures': failures_escaped_json
        }
    }

    session.set_responses(job_resp, failed_job_resp, job_resp, failed_job_resp)

    # When
    with pytest.deprecated_call():
        del_resp = project.gemd_batch_delete([uuid.UUID('16fd2706-8baf-433b-82eb-8c7fada847da')])

    # Then
    assert 2 == session.num_calls

    assert len(del_resp) == 1
    first_failure = del_resp[0]

    expected_api_error = ApiError.build({
        "code": "400",
        "message": "",
        "validation_errors": [{"failure_message": "fail msg", "failure_id": "identifier.coreid.missing"}]
    })

    assert first_failure[0] == LinkByUID('somescope', 'abcd-1234')
    assert first_failure[1].dump() == expected_api_error.dump()

    # And again with tuples of (scope, id)
    with pytest.deprecated_call():
        del_resp = project.gemd_batch_delete([LinkByUID('id', '16fd2706-8baf-433b-82eb-8c7fada847da')])
    assert len(del_resp) == 1
    first_failure = del_resp[0]

    assert first_failure[0] == LinkByUID('somescope', 'abcd-1234')
    assert first_failure[1].dump() == expected_api_error.dump()


def test_batch_delete_bad_input(project):
    with pytest.deprecated_call():
        with pytest.raises(TypeError):
            project.gemd_batch_delete([True])


def test_project_tables(project):
    assert isinstance(project.tables, GemTableCollection)


def test_owned_dataset_ids(project, datasets):
    # Create a set of datasets in the project
    ids = {uuid.uuid4() for _ in range(5)}
    for d_id in ids:
        dataset = Dataset(name=f"Test Dataset - {d_id}", summary="Test Dataset", description="Test Dataset")
        datasets.register(dataset)

    # Set the session response to have the list of dataset IDs
    project.session.set_response({'ids': list(ids)})

    # Fetch the list of UUID owned by the current project
    with pytest.deprecated_call():
        owned_ids = project.owned_dataset_ids()

    # Let's mock our expected API call so we can compare and ensure that the one made is the same
    expect_call = FakeCall(method='GET',
                           path='/DATASET/authorized-ids',
                           params={'userId': '',
                                   'domain': '/projects/16fd2706-8baf-433b-82eb-8c7fada847da',
                                   'action': 'WRITE'})
    # Compare our calls
    assert expect_call == project.session.last_call
    assert project.session.num_calls == len(ids) + 1
    assert ids == set(owned_ids)
