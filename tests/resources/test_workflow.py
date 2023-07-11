import uuid
import pytest
from datetime import datetime
from citrine.resources.design_workflow import DesignWorkflowCollection
from citrine.informatics.workflows.design_workflow import DesignWorkflow
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture(scope='module')
def basic_design_workflow_data():
    return {
        'id': str(uuid.uuid4()),
        'name': 'Test Workflow',
        'status': 'SUCCEEDED',
        'status_description': 'READY',
        'design_space_id': str(uuid.uuid4()),
        'predictor_id': str(uuid.uuid4()),
        'module_type': 'DESIGN_WORKFLOW',
        'create_time': datetime(2020, 1, 1, 1, 1, 1, 1).isoformat("T"),
        'created_by': str(uuid.uuid4()),
    }


@pytest.fixture(scope='module')
def failed_design_workflow_data(basic_design_workflow_data):
    return {
        **basic_design_workflow_data,
        'status': 'FAILED',
        'status_description': 'ERROR',
        'status_detail': [
            {'level': 'WARN', 'msg': 'Something is wrong'},
            {'level': 'Error', 'msg': 'Very wrong'}
        ]
    }


def test_build_design_workflow(basic_design_workflow_data):
    # Given
    workflow_collection = DesignWorkflowCollection(project_id=uuid.uuid4(), session=None)

    # When
    workflow = workflow_collection.build(basic_design_workflow_data)

    # Then
    assert workflow.project_id == workflow_collection.project_id
    assert workflow._session is None
    assert workflow.succeeded() and not workflow.in_progress() and not workflow.failed()


def test_list_workflows(basic_design_workflow_data):
    #Given
    session = FakeSession()
    workflow_collection = DesignWorkflowCollection(project_id=uuid.uuid4(), session=session)
    session.set_responses({'response': [basic_design_workflow_data], 'page': 1, 'per_page': 20})

    # When
    workflows = list(workflow_collection.list(per_page=20))

    # Then
    expected_design_call = FakeCall(method='GET', path='/projects/{}/modules'.format(workflow_collection.project_id),
                                   params={'per_page': 20, 'module_type': 'DESIGN_WORKFLOW'})
    assert 1 == session.num_calls
    assert len(workflows) == 1
    assert isinstance(workflows[0], DesignWorkflow)


def test_status_info(failed_design_workflow_data):
    dwc = DesignWorkflowCollection(project_id=uuid.uuid4(), session=FakeSession())
    dw = dwc.build(failed_design_workflow_data)
    with pytest.deprecated_call():
        assert dw.status_info == [status.msg for status in dw.status_detail]
