import uuid

from citrine.resources.workflow import WorkflowCollection


def test_build_workflow():
    # Given
    workflow_collection = WorkflowCollection(project_id=uuid.uuid4(), session=None)
    design_workspace_data = {
        'id': str(uuid.uuid4()),
        'display_name': 'Test Workflow',
        'status': 'READY',
        'modules': {
            'design_space_id': str(uuid.uuid4()),
            'processor_id': str(uuid.uuid4()),
            'predictor_id': str(uuid.uuid4()),
        }
    }

    # When
    workflow = workflow_collection.build(design_workspace_data)

    # Then
    assert workflow.project_id == workflow_collection.project_id
    assert workflow.session is None
