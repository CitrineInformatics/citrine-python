import pytest
from uuid import UUID

from citrine.jobs.job import TaskNode, JobStatusResponse, JobSubmissionResponse
from citrine.resources.gemtables import GemTableCollection
from citrine.resources.project import Project
from citrine.resources.table_config import TableConfig
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
def collection(session) -> GemTableCollection:
    return GemTableCollection(
        project_id=UUID('6b608f78-e341-422c-8076-35adc8828545'),
        session=session
    )


@pytest.fixture
def table_config() -> TableConfig:
    table_config = TableConfig(name="name", description="description", datasets=[], rows=[], variables=[], columns=[])
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
    assert tn.dump() == expected


def test_js_serde():
    js = JobStatusResponse.build(job_status())
    expected = job_status()
    expected['tasks'][0]['failure_reason'] = None
    expected['output'] = None
    assert js.dump() == expected


def test_js_serde_with_output():
    js = JobStatusResponse.build(job_status_with_output())
    expected = job_status_with_output()
    expected['tasks'][0]['failure_reason'] = None
    assert js.dump() == expected


def test_build_job(collection: GemTableCollection, table_config: TableConfig):
    collection.session.set_response({"job_id": '12345678-1234-1234-1234-123456789ccc'})
    resp = collection.initiate_build(table_config)
    assert isinstance(resp, JobSubmissionResponse)
    assert resp.job_id == UUID('12345678-1234-1234-1234-123456789ccc')
