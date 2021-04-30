import uuid
import pytest
from datetime import datetime
from citrine.resources.workflow import WorkflowCollection
from citrine.informatics.workflows.design_workflow import DesignWorkflow
from citrine.informatics.workflows.performance_workflow import PerformanceWorkflow
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture(scope='module')
def basic_design_workflow_data():
    return {
        'id': str(uuid.uuid4()),
        'display_name': 'Test Workflow',
        'status': 'SUCCEEDED',
        'status_description': 'READY',
        'config': {
            'design_space_id': str(uuid.uuid4()),
            'processor_id': str(uuid.uuid4()),
            'predictor_id': str(uuid.uuid4()),
        },
        'module_type': 'DESIGN_WORKFLOW',
        'create_time': datetime(2020, 1, 1, 1, 1, 1, 1).isoformat("T"),
        'created_by': str(uuid.uuid4()),
    }


@pytest.fixture(scope='module')
def basic_performance_workflow_data():
    return {
        'id': str(uuid.uuid4()),
        'display_name': 'Test Performance Workflow',
        'status': 'INPROGRESS',
        'status_description': 'VALIDATING',
        'config': {
            'analysis': {
                'name': "Some Analysis",
                'description': "This is one cool analysis",
                'n_folds': 2,
                'n_trials': 5,
                'max_rows': 100,
            },
            'type': "PerformanceWorkflow",
        },
        'module_type': 'PERFORMANCE_WORKFLOW',
        'created_by': str(uuid.uuid4()),
        'create_time': datetime(2020, 1, 1, 1, 1, 1, 1).isoformat("T")
    }


def test_build_workflow(basic_design_workflow_data):
    # Given
    workflow_collection = WorkflowCollection(project_id=uuid.uuid4(), session=None)

    # When
    workflow = workflow_collection.build(basic_design_workflow_data)

    # Then
    assert workflow.project_id == workflow_collection.project_id
    assert workflow.session is None
    assert workflow.succeeded() and not workflow.in_progress() and not workflow.failed()


def test_list_workflows(basic_design_workflow_data, basic_performance_workflow_data):
    #Given
    session = FakeSession()
    workflow_collection = WorkflowCollection(project_id=uuid.uuid4(), session=session)
    session.set_responses(
        {'entries': [basic_design_workflow_data], 'next': ''},
        {'entries': [basic_performance_workflow_data], 'next': ''},
    )

    # When
    workflows = list(workflow_collection.list(per_page=20))

    # Then
    expected_design_call = FakeCall(method='GET', path='/projects/{}/modules'.format(workflow_collection.project_id),
                                   params={'per_page': 20, 'module_type': 'DESIGN_WORKFLOW'})
    expected_performance_call = FakeCall(method='GET', path='/projects/{}/modules'.format(workflow_collection.project_id),
                                   params={'per_page': 20, 'module_type': 'PERFORMANCE_WORKFLOW'})
    assert 2 == session.num_calls
    assert expected_design_call == session.calls[0]
    assert expected_performance_call == session.calls[1]
    assert len(workflows) == 2
    assert isinstance(workflows[0], DesignWorkflow)
    assert isinstance(workflows[1], PerformanceWorkflow)
