from uuid import UUID

import pytest
from citrine.resources.ara_definition import AraDefinition, AraDefinitionCollection
from citrine.resources.ara_job import TaskNode, JobStatusResponse, JobSubmissionResponse
from citrine.resources.project import Project

from tests.utils.session import FakeSession


def task_node_1() -> dict:
    tn1 = {'id': 'dave_id1', 'task_type': 'dave_type', 'status': 'dave_status',
                   'dependencies': ['dep1', 'dep2']}
    return tn1


def task_node_2() -> dict:
    tn2 = {'id': 'dave_id2', 'task_type': 'dave_type', 'status': 'dave_status', 'failure_reason': 'because I failed',
                   'dependencies': ['dep3', 'dep4']}
    return tn2


def job_status() -> dict:
    js = {'job_type': "dave_job_type", 'status': "david_job_status", "tasks": [task_node_1(), task_node_2()]}
    return js


def job_status_with_output() -> dict:
    js = {'job_type': "dave_job_type",
          'status': "david_job_status",
          "tasks": [task_node_1(), task_node_2()],
          "output": {"key1": "val1", "key2": "val2"}
          }
    return js


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def collection(session) -> AraDefinitionCollection:
    return AraDefinitionCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        session=session
    )


@pytest.fixture
def table_config() -> AraDefinition:
    table_config: AraDefinition = AraDefinition(name="name", description="description", datasets=[], rows=[], variables=[], columns=[])
    table_config.version_number = 1
    table_config.config_uid = UUID('12345678-1234-1234-1234-123456789bbb')
    return table_config


@pytest.fixture
def project(session: FakeSession) -> Project:
    project = Project(
        name="Test GEM Tables project",
        session=session
    )
    project.uid = UUID('6b608f78-e341-422c-8076-35adc8828545')
    return project


def test_tn_serde():
    tn = TaskNode.build(task_node_1())
    expected = task_node_1()
    expected['failure_reason'] = None
    expected_tn = TaskNode(
        id=expected['id'],
        task_type=expected['task_type'],
        status=expected['status'],
        dependencies=expected['dependencies'],
        failure_reason=expected['failure_reason']
    )
    assert tn.dump() == expected_tn.dump()


def test_js_serde():
    js = JobStatusResponse.build(job_status())
    expected = job_status()
    expected['tasks'][0]['failure_reason'] = None
    expected['output'] = None
    expected_js = JobStatusResponse(
        job_type=expected['job_type'],
        status=expected['status'],
        tasks=[TaskNode.build(i) for i in expected['tasks']],
        output=expected['output']
    )
    assert js.dump() == expected_js.dump()


def test_js_serde_with_output():
    js = JobStatusResponse.build(job_status_with_output())
    expected = job_status_with_output()
    expected['tasks'][0]['failure_reason'] = None
    expected_js = JobStatusResponse(
        job_type=expected['job_type'],
        status=expected['status'],
        tasks=[TaskNode.build(i) for i in expected['tasks']],
        output={"key1": "val1", "key2": "val2"}
    )
    assert js.dump() == expected_js.dump()


def test_build_job(collection: AraDefinitionCollection, table_config: AraDefinition):
    collection.session.set_response({"job_id": '12345678-1234-1234-1234-123456789ccc'})
    resp = collection.build_ara_table(table_config)
    assert resp.dump() == JobSubmissionResponse(UUID('12345678-1234-1234-1234-123456789ccc')).dump()


def test_job_status(collection: AraDefinitionCollection):
    status = job_status()
    collection.session.set_response(status)
    resp = collection.get_job_status(job_id='12345678-1234-1234-1234-123456789ccc')
    status['tasks'][0]['failure_reason'] = None
    status['output'] = None
    assert status == resp.dump()


def test_job_status_with_output(collection: AraDefinitionCollection):
    status = job_status_with_output()
    collection.session.set_response(status)
    resp = collection.get_job_status(job_id='12345678-1234-1234-1234-123456789ccc')
    status['tasks'][0]['failure_reason'] = None
    assert status == resp.dump()
