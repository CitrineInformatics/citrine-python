import pytest
from citrine.resources.ara_job import TaskNode, JobStatusResponse


def task_node_1() -> dict:
    tn1 = {'id': 'dave_id1', 'task_type': 'dave_type', 'status': 'dave_status',
                   'dependencies': {'dep1', 'dep2'}}
    return tn1


def task_node_2() -> dict:
    tn2 = {'id': 'dave_id2', 'task_type': 'dave_type', 'status': 'dave_status', 'failure_reason': 'because I failed',
                   'dependencies': ['dep3', 'dep4']}
    return tn2


def job_status() -> dict:
    js = {'job_type': "dave_job_type", 'status': "david_job_status", "tasks": [task_node_1(), task_node_2()]}
    return js


def test_tn_serde():
    tn = TaskNode.build(task_node_1())
    assert tn.dump() == task_node_1()


def test_js_serde():
    js = JobStatusResponse.build(job_status())
    assert js.dump() == job_status()
