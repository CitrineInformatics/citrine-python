"""Tests of the Project schema."""
import pytest
from datetime import datetime
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
        active=True,
        config=dict(
            design_space_id=str(uuid4()),
            processor_id=str(uuid4()),
            predictor_id=str(uuid4()),
        ),
        module_type='DESIGN_WORKFLOW',
        schema_id='8af8b007-3e81-4185-82b2-6f62f4a2e6f1',
        created_by=str(uuid4()),
        create_time=datetime(2020, 1, 1, 1, 1, 1, 1).isoformat("T")
    )


@pytest.fixture
def valid_serialization_output(valid_data):
    return {x: y for x, y in valid_data.items() if x not in ['status', 'status_info', 'created_by', 'create_time']}


def test_simple_deserialization(valid_data):
    """Ensure a deserialized DesignWorkflow looks sane."""
    workflow: DesignWorkflow = DesignWorkflow.build(valid_data)
    assert workflow.design_space_id == UUID(valid_data['config']['design_space_id'])
    assert workflow.processor_id == UUID(valid_data['config']['processor_id'])
    assert workflow.predictor_id == UUID(valid_data['config']['predictor_id'])


def test_roundtrip_without_processor(valid_data, valid_serialization_output):
    """Ensure a deserialized DesignWorkflow without a processor looks sane."""
    valid_data['config']['processor_id'] = None
    workflow: DesignWorkflow = DesignWorkflow.build(valid_data)
    assert workflow.design_space_id == UUID(valid_data['config']['design_space_id'])
    assert workflow.processor_id is None
    assert workflow.predictor_id == UUID(valid_data['config']['predictor_id'])
    serialized = workflow.dump()
    serialized['id'] = valid_data['id']
    valid_serialization_output['config']['processor_id'] = None
    assert serialized == valid_serialization_output


def test_deserialization_missing_created_by(valid_data):
    """Ensure a DesignWorkflow can be deserialized with no created_by field."""
    valid_data['created_by'] = None
    workflow: DesignWorkflow = DesignWorkflow.build(valid_data)

    assert workflow.design_space_id == UUID(valid_data['config']['design_space_id'])
    assert workflow.created_by is None


def test_deserialization_missing_create_time(valid_data):
    """Ensure a DesignWorkflow can be deserialized with no created_by field."""
    valid_data['create_time'] = None
    workflow: DesignWorkflow = DesignWorkflow.build(valid_data)

    assert workflow.design_space_id == UUID(valid_data['config']['design_space_id'])
    assert workflow.create_time is None


def test_polymorphic_deserialization(valid_data):
    """Ensure a polymorphically deserialized designWorkflow looks sane."""
    workflow: DesignWorkflow = Workflow.build(valid_data)
    assert workflow.design_space_id == UUID(valid_data['config']['design_space_id'])
    assert workflow.processor_id == UUID(valid_data['config']['processor_id'])
    assert workflow.predictor_id == UUID(valid_data['config']['predictor_id'])


def test_serialization(valid_data, valid_serialization_output):
    """Ensure a serialized DesignWorkflow looks sane."""
    workflow: DesignWorkflow = Workflow.build(valid_data)
    serialized = workflow.dump()
    serialized['id'] = valid_data['id']
    assert serialized == valid_serialization_output
