"""Tests of the Project schema."""
import pytest
from datetime import datetime
from uuid import uuid4, UUID
from citrine.informatics.workflows import DesignWorkflow


@pytest.fixture
def valid_data():
    """Return valid data used for these tests."""
    return dict(
        id=str(uuid4()),
        name='A rad new workflow',
        description='All about my workflow',
        status='SUCCEEDED',
        status_description='READY',
        status_detail=[{'level': 'Info', 'msg': 'Things are looking good'}],
        archived=False,
        design_space_id=str(uuid4()),
        predictor_id=str(uuid4()),
        created_by=str(uuid4()),
        create_time=datetime(2020, 1, 1, 1, 1, 1, 1).isoformat("T")
    )


@pytest.fixture
def valid_serialization_output(valid_data):
    return {x: y for x, y in valid_data.items() if x not in
            ['status', 'status_detail', 'status_description', 'created_by', 'create_time']}


def test_simple_deserialization(valid_data):
    """Ensure a deserialized DesignWorkflow looks sane."""
    workflow: DesignWorkflow = DesignWorkflow.build(valid_data)
    assert workflow.design_space_id == UUID(valid_data['design_space_id'])
    assert workflow.predictor_id == UUID(valid_data['predictor_id'])


def test_deserialization_missing_created_by(valid_data):
    """Ensure a DesignWorkflow can be deserialized with no created_by field."""
    valid_data['created_by'] = None
    workflow: DesignWorkflow = DesignWorkflow.build(valid_data)

    assert workflow.design_space_id == UUID(valid_data['design_space_id'])
    assert workflow.created_by is None


def test_deserialization_missing_create_time(valid_data):
    """Ensure a DesignWorkflow can be deserialized with no created_by field."""
    valid_data['create_time'] = None
    workflow: DesignWorkflow = DesignWorkflow.build(valid_data)

    assert workflow.design_space_id == UUID(valid_data['design_space_id'])
    assert workflow.create_time is None


def test_serialization(valid_data, valid_serialization_output):
    """Ensure a serialized DesignWorkflow looks sane."""
    workflow: DesignWorkflow = DesignWorkflow.build(valid_data)
    serialized = workflow.dump()
    serialized['id'] = valid_data['id']
    # we can have extra fields in the output of `dump`
    # these support forwards and backwards compatibility
    for k in valid_serialization_output:
        assert serialized[k] == valid_serialization_output[k]
