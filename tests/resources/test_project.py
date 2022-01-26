import uuid
from logging import getLogger
from unittest import mock

import pytest
from dateutil.parser import parse
from gemd.entity.link_by_uid import LinkByUID

from citrine.exceptions import NotFound, ModuleRegistrationFailedException
from citrine.resources.api_error import ApiError, ValidationError
from citrine.resources.dataset import Dataset
from citrine.resources.gemtables import GemTableCollection
from citrine.resources.process_spec import ProcessSpec
from citrine.resources.project import Project, ProjectCollection
from citrine.resources.project_member import ProjectMember
from citrine.resources.project_roles import MEMBER, LEAD, WRITE
from tests.utils.factories import ProjectDataFactory, UserDataFactory
from tests.utils.session import FakeSession, FakeCall, FakePaginatedSession, FakeRequestResponse

logger = getLogger(__name__)


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def session_v3() -> FakeSession:
    return FakeSession(accounts_v3=True)


@pytest.fixture
def paginated_session() -> FakePaginatedSession:
    return FakePaginatedSession()


@pytest.fixture
def paginated_session_accounts_v3() -> FakeSession:
    return FakePaginatedSession(accounts_v3=True)


@pytest.fixture
def paginated_collection(paginated_session) -> ProjectCollection:
    return ProjectCollection(
        session=paginated_session
    )


@pytest.fixture
def project(session) -> Project:
    project = Project(
        name='Test Project',
        session=session
    )
    project.uid = uuid.UUID('16fd2706-8baf-433b-82eb-8c7fada847da')
    return project


@pytest.fixture
def project_v3(session_v3) -> Project:
    project = Project(
        name='Test Project',
        session=session_v3,
        team_id=uuid.UUID('11111111-8baf-433b-82eb-8c7fada847da')
    )
    project.uid = uuid.UUID('16fd2706-8baf-433b-82eb-8c7fada847da')
    return project


@pytest.fixture
def collection(session) -> ProjectCollection:
    return ProjectCollection(session)


@pytest.fixture
def collection_v3(session_v3) -> ProjectCollection:
    return ProjectCollection(session_v3, team_id=uuid.uuid4())


def test_string_representation(project):
    assert "<Project 'Test Project'>" == str(project)


def test_share_post_content_v3(project_v3):
    # Given
    dataset_id = str(uuid.uuid4())
    other_project_id = uuid.uuid4()

    with pytest.raises(NotImplementedError):
        project_v3.share(project_id=other_project_id, resource_type='DATASET', resource_id=dataset_id)


def test_share_post_content(project, session):
    # Given
    dataset_id = str(uuid.uuid4())

    # When
    # Share using resource type/id, which is deprecated
    with pytest.warns(DeprecationWarning):
        project.share(project_id=project.uid, resource_type='DATASET', resource_id=dataset_id)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/projects/{}/share'.format(project.uid),
        json={
            'project_id': str(project.uid),
            'resource': {'type': 'DATASET', 'id': dataset_id}
        }
    )
    assert expected_call == session.last_call

    # Share by resource
    # When
    dataset = Dataset(name="foo", summary="", description="")
    dataset.uid = str(uuid.uuid4())
    project.share(resource=dataset, project_id=project.uid)

    # Then
    assert 2 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/projects/{}/share'.format(project.uid),
        json={
            'project_id': str(project.uid),
            'resource': {'type': 'DATASET', 'id': str(dataset.uid)}
        }
    )
    assert expected_call == session.last_call

    # providing both the resource and the type/id is an error
    with pytest.warns(DeprecationWarning):
        with pytest.raises(ValueError):
            project.share(resource=dataset, project_id=project.uid, resource_type='DATASET', resource_id=dataset_id)

    # Providing neither the resource nor the type/id is an error
    with pytest.raises(ValueError):
        project.share(project_id=project.uid)


def test_publish_resource(project, session):
    dataset_id = str(uuid.uuid4())
    dataset = project.datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))

    with pytest.raises(NotImplementedError):
        project.publish(resource=dataset)


def test_publish_resource_v3(project_v3, session_v3):
    dataset_id = str(uuid.uuid4())
    dataset = project_v3.datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))
    assert project_v3.publish(resource=dataset)

    assert 1 == session_v3.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/projects/{}/published-resources/{}/batch-publish'.format(project_v3.uid, 'DATASET'),
        json={
            'ids': [dataset_id]
        }
    )
    assert expected_call == session_v3.last_call


def test_pull_in_resource(project, session):
    dataset_id = str(uuid.uuid4())
    dataset = project.datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))

    with pytest.raises(NotImplementedError):
        project.pull_in_resource(resource=dataset)


def test_pull_in_resource_v3(project_v3, session_v3):
    dataset_id = str(uuid.uuid4())
    dataset = project_v3.datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))
    assert project_v3.pull_in_resource(resource=dataset)

    assert 1 == session_v3.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'/teams/{project_v3.team_id}/projects/{project_v3.uid}/outside-resources/DATASET/batch-pull-in',
        json={
            'ids': [dataset_id]
        }
    )
    assert expected_call == session_v3.last_call


def test_un_publish_resource(project, session):
    dataset_id = str(uuid.uuid4())
    dataset = project.datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))

    with pytest.raises(NotImplementedError):
        project.un_publish(resource=dataset)


def test_un_publish_resource_v3(project_v3, session_v3):
    dataset_id = str(uuid.uuid4())
    dataset = project_v3.datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))
    assert project_v3.un_publish(resource=dataset)

    assert 1 == session_v3.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/projects/{}/published-resources/{}/batch-un-publish'.format(project_v3.uid, 'DATASET'),
        json={
            'ids': [dataset_id]
        }
    )
    assert expected_call == session_v3.last_call


def test_make_resource_public_v3(project_v3):
    dataset_id = str(uuid.uuid4())
    dataset = project_v3.datasets.build(dict(
        id=dataset_id,
        name="public dataset", summary="test", description="test"
    ))

    with pytest.raises(NotImplementedError):
        project_v3.make_public(dataset)


def test_make_resource_public(project, session):
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

    with pytest.raises(RuntimeError):
        project.make_public(ProcessSpec("dummy process"))


def test_make_resource_private_v3(project_v3):
    dataset_id = str(uuid.uuid4())
    dataset = project_v3.datasets.build(dict(
        id=dataset_id,
        name="private dataset", summary="test", description="test"
    ))
    with pytest.raises(NotImplementedError):
        project_v3.make_private(dataset)


def test_make_resource_private(project, session):
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

    with pytest.raises(RuntimeError):
        project.make_private(ProcessSpec("dummy process"))


def test_transfer_resource_v3(project_v3):

    dataset_id = str(uuid.uuid4())
    other_project_id = uuid.uuid4()
    dataset = project_v3.datasets.build(dict(
        id=dataset_id,
        name="dataset to transfer", summary="test", description="test"
    ))

    with pytest.raises(NotImplementedError):
        project_v3.transfer_resource(resource=dataset, receiving_project_uid=other_project_id)


def test_transfer_resource(project, session):

    dataset_id = str(uuid.uuid4())
    dataset = project.datasets.build(dict(
        id=dataset_id,
        name="dataset to transfer", summary="test", description="test"
    ))

    assert project.transfer_resource(resource=dataset, receiving_project_uid=project.uid)

    expected_call = FakeCall(
        method='POST',
        path='/projects/{}/transfer-resource'.format(project.uid),
        json={
            'to_project_id': str(project.uid),
            'resource': dataset.access_control_dict()
        }
    )
    assert expected_call == session.last_call

    with pytest.raises(RuntimeError):
        project.transfer_resource(resource=ProcessSpec("dummy process"), receiving_project_uid=project.uid)


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


def test_gemd_resource_get_project_id(project):
    assert project.uid == project.gemd.project_id


def test_design_spaces_get_project_id(project):
    assert project.uid == project.design_spaces.project_id


def test_modules_get_project_id(project):
    assert project.uid == project.modules.project_id


def test_descriptors_get_project_id(project):
    assert project.uid == project.descriptors.project_id


def test_processors_get_project_id(project):
    assert project.uid == project.processors.project_id


def test_predictors_get_project_id(project):
    assert project.uid == project.predictors.project_id


def test_pe_workflows_get_project_id(project):
    assert project.uid == project.predictor_evaluation_workflows.project_id


def test_pe_executions_get_project_id(project):
    assert project.uid == project.predictor_evaluation_executions.project_id
    # The resulting collection cannot be used to trigger executions.
    with pytest.raises(RuntimeError):
        project.predictor_evaluation_executions.trigger(uuid.uuid4())


def test_design_workflows_get_project_id(project):
    assert project.uid == project.design_workflows.project_id


def test_design_workflows_get_branch_id(project):
    assert None is project.design_workflows.branch_id


def test_branches_get_project_id(project):
    assert project.uid == project.branches.project_id


def test_ara_definitions_get_project_id(project):
    assert project.uid == project.table_configs.project_id


def test_project_registration_v3(collection: ProjectCollection, session):
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


def test_failed_register_v3():
    team_id = uuid.uuid4()
    session = mock.Mock()
    session.post_resource.side_effect = NotFound(f'/teams/{team_id}/projects',
                                                 FakeRequestResponse(400))
    project_collection = ProjectCollection(session=session, team_id=team_id)
    with pytest.raises(ModuleRegistrationFailedException) as e:
        project_collection.register("Project")
    assert 'The "Project" failed to register.' in str(e.value)
    assert f'/teams/{team_id}/projects' in str(e.value)


def test_failed_register_v3_no_team(session_v3):
    project_collection = ProjectCollection(session=session_v3)
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

    # When
    created_project = collection.register('testing')

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(
        method='POST',
        path='/projects',
        json={
            'name': 'testing'
        }
    )
    assert expected_call == session.last_call

    assert 'A sample project' == created_project.description
    assert 'CREATED' == created_project.status
    assert create_time == created_project.created_at


def test_project_registration_v3(collection_v3: ProjectCollection, session_v3):
    # Given
    create_time = parse('2019-09-10T00:00:00+00:00')
    project_data = ProjectDataFactory(
        name='testing',
        description='A sample project',
        created_at=int(create_time.timestamp() * 1000)  # The lib expects ms since epoch, which is really odd
    )
    session_v3.set_response({'project': project_data})
    team_id = collection_v3.team_id

    # When
    created_project = collection_v3.register('testing')

    # Then
    assert 1 == session_v3.num_calls
    expected_call = FakeCall(
        method='POST',
        path=f'teams/{team_id}/projects',
        json={
            'name': 'testing'
        }
    )
    assert expected_call == session_v3.last_call

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
    expected_call = FakeCall(method='GET', path='/projects', params={'per_page': 1000})
    assert expected_call == session.last_call
    assert 5 == len(projects)


def test_list_projects_v3(collection_v3, session_v3):
    # Given
    projects_data = ProjectDataFactory.create_batch(5)
    session_v3.set_response({'projects': projects_data})

    # When
    projects = list(collection_v3.list())

    # Then
    assert 1 == session_v3.num_calls
    expected_call = FakeCall(method='GET', path=f'/teams/{collection_v3.team_id}/projects', params={'per_page': 1000})
    assert expected_call == session_v3.last_call
    assert 5 == len(projects)


def test_failed_list_v3_no_team(session_v3):
    project_collection = ProjectCollection(session=session_v3)
    with pytest.raises(NotImplementedError):
        project_collection.list()


def test_list_projects_filters_non_projects(collection, session):
    # Given
    projects_data = ProjectDataFactory.create_batch(5)
    projects_data.append({'foo': 'not a project'})
    session.set_response({'projects': projects_data})

    # Then
    with pytest.raises(RuntimeError):
        # When
        list(collection.list())


def test_list_projects_with_page_params(collection, session):
    # Given
    project_data = ProjectDataFactory()
    session.set_response({'projects': [project_data]})

    # When
    list(collection.list(per_page=10))

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='GET', path='/projects', params={'per_page': 10})
    assert expected_call == session.last_call


def test_search_projects_v3(collection_v3: ProjectCollection):
    # TODO: This tests needs proper mocking before it can be used
    # Given
    # search_params = {'search_params': {
    #     'name': {
    #         'value': 'Some Name',
    #         'search_method': 'EXACT'}}}

    # Then
    # collection = collection_v3.search(search_params=search_params)
    # with pytest.raises(NotImplementedError):
    #     list(collection_v3.search(search_params=search_params))
    pytest.skip("Not yet implemented, only compatible with accounts V3")


def test_search_projects(collection: ProjectCollection, session):
    # Given
    projects_data = ProjectDataFactory.create_batch(2)

    project_name_to_match = projects_data[0]['name']

    expected_response = list(filter(lambda p: p["name"] == project_name_to_match, projects_data))

    session.set_response({'projects': expected_response})

    search_params = {'name': {
        'value': project_name_to_match,
        'search_method': 'EXACT'}}

    # When
    projects = list(collection.search(search_params=search_params))

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='POST', path='/projects/search', 
                             params={'per_page': 1000}, json={'search_params': search_params})
    assert expected_call == session.last_call
    assert len(expected_response) == len(projects)


def test_search_projects_with_pagination(paginated_collection: ProjectCollection, paginated_session):
    # Given
    common_name = "same name"

    same_name_projects_data = ProjectDataFactory.create_batch(35, name=common_name)
    ProjectDataFactory.create_batch(35, name="some other name")

    per_page = 10

    paginated_session.set_response({'projects': same_name_projects_data})

    search_params = {'status': {
        'value': common_name,
        'search_method': 'EXACT'}}

    # When
    projects = list(paginated_collection.search(per_page=per_page, search_params=search_params))

    # Then
    assert 4 == paginated_session.num_calls
    expected_first_call = FakeCall(method='POST', path='/projects/search', 
                                   params={'per_page': per_page}, json={'search_params': search_params})
    expected_last_call = FakeCall(method='POST', path='/projects/search', 
                                  params={'page': 4, 'per_page': per_page}, json={'search_params': search_params})

    assert expected_first_call == paginated_session.calls[0]
    assert expected_last_call == paginated_session.last_call

    project_ids = [str(p.uid) for p in projects]
    expected_ids = [p['id'] for p in same_name_projects_data]

    assert project_ids == expected_ids


def test_delete_project(collection, session):
    # Given
    uid = '151199ec-e9aa-49a1-ac8e-da722aaf74c4'

    # When
    collection.delete(uid)

    # Then
    assert 1 == session.num_calls
    expected_call = FakeCall(method='DELETE', path='/projects/{}'.format(uid))
    assert expected_call == session.last_call


def test_update_project(collection: ProjectCollection, project):
    project.name = "updated name"
    with pytest.raises(NotImplementedError):
        collection.update(project)


def test_list_members_v3(project_v3):
    with pytest.raises(NotImplementedError):
        project_v3.list_members()


def test_list_members(project, session):
    # Given
    user = UserDataFactory()
    user["role"] = MEMBER
    session.set_response({'users': [user]})

    # When
    members = project.list_members()

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method='GET', path='/projects/{}/users'.format(project.uid))
    assert expect_call == session.last_call
    assert isinstance(members[0], ProjectMember)


def test_update_user_role_v3(project_v3):
    # Given
    user_id = uuid.uuid4()

    # Then
    with pytest.raises(NotImplementedError):
        project_v3.update_user_role(user_uid=user_id, role=LEAD)


def test_update_user_role(project, session):
    # Given
    user = UserDataFactory()
    session.set_response({'actions': [], 'role': 'LEAD'})

    # When
    update_user_role_response = project.update_user_role(user_uid=user["id"], role=LEAD)

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method="POST", path="/projects/{}/users/{}".format(project.uid, user["id"]),
                           json={'role': LEAD, 'actions': []})
    assert expect_call == session.last_call
    assert update_user_role_response is True


def test_update_user_actions(project, session):
    # Given
    user = UserDataFactory()
    session.set_response({'actions': ['READ'], 'role': 'LEAD'})

    # When
    update_user_role_response = project.update_user_role(user_uid=user["id"], role=LEAD, actions=[WRITE])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method="POST", path="/projects/{}/users/{}".format(project.uid, user["id"]),
                           json={'role': LEAD, 'actions': [WRITE]})
    assert expect_call == session.last_call
    assert update_user_role_response is True


def test_add_user_v3(project_v3):
    # Given
    user_id = uuid.uuid4()

    # Then
    with pytest.raises(NotImplementedError):
        project_v3.add_user(user_id)


def test_add_user(project, session):
    # Given
    user = UserDataFactory()
    session.set_response({'actions': [], 'role': 'MEMBER'})

    # When
    add_user_response = project.add_user(user["id"])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method="POST", path='/projects/{}/users/{}'.format(project.uid, user["id"]), json={
        "role": "MEMBER",
        "actions": []
    })
    assert expect_call == session.last_call
    assert add_user_response is True


def test_remove_user_v3(project_v3):
    # Given
    user_id = uuid.uuid4()

    # Then
    with pytest.raises(NotImplementedError):
        project_v3.remove_user(user_id)


def test_remove_user(project, session):
    # Given
    user = UserDataFactory()

    # When
    remove_user_response = project.remove_user(user["id"])

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(
        method="DELETE",
        path="/projects/{}/users/{}".format(project.uid, user["id"])
    )
    assert expect_call == session.last_call
    assert remove_user_response is True


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
    del_resp = project.gemd_batch_delete([uuid.UUID(
        '16fd2706-8baf-433b-82eb-8c7fada847da')])

    # Then
    assert len(del_resp) == 0

    # When trying with entities
    session.set_responses(job_resp, successful_job_resp)
    entity = ProcessSpec(name="proc spec", uids={'id': '16fd2706-8baf-433b-82eb-8c7fada847da'})
    del_resp = project.gemd_batch_delete([entity])

    # Then
    assert len(del_resp) == 0


def test_project_batch_delete(project, session):
    job_resp = {
        'job_id': '1234'
    }

    import json
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
    del_resp = project.gemd_batch_delete([uuid.UUID(
        '16fd2706-8baf-433b-82eb-8c7fada847da')])

    # Then
    assert 2 == session.num_calls

    assert len(del_resp) == 1
    first_failure = del_resp[0]

    expected_api_error = ApiError(400, "",
                                  validation_errors=[ValidationError(
                                      failure_message="fail msg",
                                      failure_id="identifier.coreid.missing")])

    assert first_failure == (LinkByUID('somescope', 'abcd-1234'), expected_api_error)

    # And again with tuples of (scope, id)
    del_resp = project.gemd_batch_delete([LinkByUID('id',
                                                    '16fd2706-8baf-433b-82eb-8c7fada847da')])
    assert len(del_resp) == 1
    first_failure = del_resp[0]

    assert first_failure == (LinkByUID('somescope', 'abcd-1234'), expected_api_error)


def test_batch_delete_bad_input(project):
    with pytest.raises(TypeError):
        project.gemd_batch_delete([True])


def test_project_tables(project):
    assert isinstance(project.tables, GemTableCollection)


def test_creator_v3(project_v3):
    with pytest.raises(NotImplementedError):
        project_v3.creator()


def test_creator(project, session):
    # Given
    email = 'CaTiO3@perovskite.com'
    session.set_response({'email': email})

    # When
    creator = project.creator()

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method='GET', path='/projects/{}/creator'.format(project.uid))
    assert expect_call == session.last_call
    assert creator == email


def test_owned_dataset_ids(project, session):
    # Given
    id_set = {uuid.uuid4() for _ in range(5)}
    session.set_response({'dataset_ids': list(id_set)})

    # When
    ids = project.owned_dataset_ids()

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method='GET', path='/projects/{}/dataset_ids'.format(project.uid))
    assert expect_call == session.last_call
    assert all(x in id_set for x in ids)
    assert len(ids) == len(id_set)


def test_owned_table_ids(project, session):
    # Given
    id_set = {uuid.uuid4() for _ in range(5)}
    session.set_response({'table_ids': list(id_set)})

    # When
    ids = project.owned_table_ids()

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method='GET', path='/projects/{}/table_ids'.format(project.uid))
    assert expect_call == session.last_call
    assert all(x in id_set for x in ids)
    assert len(ids) == len(id_set)


def test_owned_table_config_ids(project, session):
    # Given
    id_set = {uuid.uuid4() for _ in range(5)}
    session.set_response({'table_definition_ids': list(id_set)})

    # When
    ids = project.owned_table_config_ids()

    # Then
    assert 1 == session.num_calls
    expect_call = FakeCall(method='GET', path='/projects/{}/table_definition_ids'.format(project.uid))
    assert expect_call == session.last_call
    assert all(x in id_set for x in ids)
    assert len(ids) == len(id_set)


def test_owned_dataset_ids_v3(project_v3):
    # TODO: This tests needs proper mocking before it can be used
    # with pytest.raises(NotImplementedError):
    #     project_v3.owned_dataset_ids()
    pytest.skip("Not yet implemented, only compatible with accounts V3")


def test_owned_table_ids_v3(project_v3):
    with pytest.raises(NotImplementedError):
        project_v3.owned_table_ids()


def test_owned_table_config_ids_v3(project_v3):
    with pytest.raises(NotImplementedError):
        project_v3.owned_table_config_ids()
