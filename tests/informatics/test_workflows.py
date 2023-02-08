"""Tests for citrine.informatics.workflows."""
from uuid import uuid4

import pytest

from citrine.resources.design_workflow import DesignWorkflowCollection
from citrine._session import Session
from citrine.informatics.workflows import DesignWorkflow, Workflow
from citrine.resources.design_execution import DesignExecutionCollection
from tests.utils.session import FakeSession


@pytest.fixture
def collection() -> DesignWorkflowCollection:
    return DesignWorkflowCollection(
        project_id=uuid4(),
        session=FakeSession(),
    )


PROJECT_ID = uuid4()


@pytest.fixture
def design_workflow(collection, design_workflow_dict) -> DesignWorkflow:
    return collection.build(design_workflow_dict)


def test_d_workflow_str(design_workflow):
    assert str(design_workflow) == f'<DesignWorkflow \'{design_workflow.name}\'>'


def test_workflow_executions_with_project(design_workflow):
    assert isinstance(design_workflow.design_executions, DesignExecutionCollection)


def test_workflow_executions_without_project():
    workflow = DesignWorkflow(
        name="workflow",
        design_space_id=uuid4(),
        predictor_id=uuid4()
    )
    with pytest.raises(AttributeError):
        workflow.design_executions
