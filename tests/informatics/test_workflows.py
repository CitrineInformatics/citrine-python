"""Tests for citrine.informatics.workflows."""
from uuid import uuid4

import pytest

from citrine._session import Session
from citrine.informatics.workflows import DesignWorkflow, Workflow
from citrine.resources.design_execution import DesignExecutionCollection

DESIGN_SPACE_ID = uuid4()
PROCESSOR_ID = uuid4()
PREDICTOR_ID = uuid4()
PROJECT_ID = uuid4()


@pytest.fixture
def design_workflow() -> DesignWorkflow:
    return DesignWorkflow('foo', DESIGN_SPACE_ID, PROCESSOR_ID, PREDICTOR_ID, PROJECT_ID)


def test_missing_module_type():
    with pytest.raises(ValueError):
        Workflow.build(dict(module_type='foo'))


def test_workflow_initialization(design_workflow):
    """Make sure the correct fields go to the correct places."""
    assert design_workflow.name == 'foo'
    assert design_workflow.design_space_id == DESIGN_SPACE_ID
    assert design_workflow.processor_id == PROCESSOR_ID
    assert design_workflow.predictor_id == PREDICTOR_ID
    assert isinstance(design_workflow.session, Session)


def test_d_workflow_str(design_workflow):
    assert str(design_workflow) == '<DesignWorkflow \'foo\'>'


def test_workflow_executions_with_project(design_workflow):
    assert isinstance(design_workflow.design_executions, DesignExecutionCollection)


def test_workflow_executions_without_project():
    workflow = DesignWorkflow(
        name="workflow",
        design_space_id=uuid4(),
        processor_id=uuid4(),
        predictor_id=uuid4()
    )
    with pytest.raises(AttributeError):
        workflow.design_executions
