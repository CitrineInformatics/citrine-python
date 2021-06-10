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
        'processor_id': str(uuid.uuid4()),
        'predictor_id': str(uuid.uuid4()),
        'module_type': 'DESIGN_WORKFLOW',
        'create_time': datetime(2020, 1, 1, 1, 1, 1, 1).isoformat("T"),
        'created_by': str(uuid.uuid4()),
    }


def test_build_design_workflow(basic_design_workflow_data):
    # Given
    workflow_collection = DesignWorkflowCollection(project_id=uuid.uuid4(), session=None)

    # When
    workflow = workflow_collection.build(basic_design_workflow_data)

    # Then
    assert workflow.project_id == workflow_collection.project_id
    assert workflow._session is None


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
