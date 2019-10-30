"""Tests of the Project schema."""
import pytest
from uuid import uuid4, UUID
from citrine.informatics.workflows import Workflow, DesignWorkflow


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        id=str(uuid4()),
        display_name='A rad new workflow',
        status='READY',
        status_info=['Things are looking good'],
        modules=dict(
            design_space_id=str(uuid4()),
            processor_id=str(uuid4()),
            predictor_id=str(uuid4()),
        )
    )


@pytest.fixture
def valid_serialization_output(valid_data):
    return { x: y for x, y in valid_data.items() if x not in ['status', 'status_info']}


def test_simple_deserialization(valid_data):
    """Ensure a deserialized DesignWorkflow looks sane."""
    workflow: DesignWorkflow = DesignWorkflow.build(valid_data)
    assert workflow.design_space_id == UUID(valid_data['modules']['design_space_id'])
    assert workflow.processor_id == UUID(valid_data['modules']['processor_id'])
    assert workflow.predictor_id == UUID(valid_data['modules']['predictor_id'])


def test_polymorphic_deserialization(valid_data):
    """Ensure a polymorphically deserialized designWorkflow looks sane."""
    workflow: DesignWorkflow = Workflow.build(valid_data)
    assert workflow.design_space_id == UUID(valid_data['modules']['design_space_id'])
    assert workflow.processor_id == UUID(valid_data['modules']['processor_id'])
    assert workflow.predictor_id == UUID(valid_data['modules']['predictor_id'])


def test_serialization(valid_data, valid_serialization_output):
    """Ensure a serialized DesignWorkflow looks sane."""
    workflow: DesignWorkflow = Workflow.build(valid_data)
    serialized = workflow.dump()
    serialized['id'] = valid_data['id']
    assert serialized == valid_serialization_output
