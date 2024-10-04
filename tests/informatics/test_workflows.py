"""Tests for citrine.informatics.workflows."""
from multiprocessing.reduction import register
from uuid import uuid4, UUID

import pytest

from citrine.informatics.design_candidate import DesignMaterial, DesignCandidate, ChemicalFormula, \
    MeanAndStd, TopCategories, Mixture, MolecularStructure
from citrine.informatics.executions import DesignExecution
from citrine.informatics.predict_request import PredictRequest
from citrine.informatics.workflows import DesignWorkflow
from citrine.resources.design_execution import DesignExecutionCollection
from citrine.resources.design_workflow import DesignWorkflowCollection

from tests.utils.factories import BranchDataFactory, DesignWorkflowDataFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def branch_data():
    return BranchDataFactory()

@pytest.fixture
def session() -> FakeSession:
    return FakeSession()

@pytest.fixture
def collection(session, branch_data) -> DesignWorkflowCollection:
    session.set_response(branch_data)

    return DesignWorkflowCollection(
        project_id=uuid4(),
        session=session,
    )


@pytest.fixture
def execution_collection(session) -> DesignExecutionCollection:
    return DesignExecutionCollection(
        project_id=uuid4(),
        session=session,
    )


PROJECT_ID = uuid4()


@pytest.fixture
def design_workflow(collection) -> DesignWorkflow:
    return collection.build(DesignWorkflowDataFactory(register=True))

@pytest.fixture
def design_execution(execution_collection, design_execution_dict) -> DesignExecution:
    return execution_collection.build(design_execution_dict)


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


def test_design_material():
    values = {
        "RealValue": MeanAndStd(mean=1.4,std=.3),
        "Cat": TopCategories(probabilities={
            "Red": 0.85,
            "Blue": 0.15
        }),
        "Mixture": Mixture(quantities={
            "Water": 0.5,
            "Active": 0.5
        }),
        "Formula": ChemicalFormula(formula="NaCl"),
        "Organic": MolecularStructure(smiles="CCO")
    }
    material = DesignMaterial(values=values)
    assert material.values == values


def test_predict(design_workflow, design_execution, example_candidates):
    session = design_execution._session

    candidate = DesignCandidate.build(example_candidates['response'][0])

    material_id = UUID("9953cc63-5d53-4d0a-884a-a9cff3b7de18")
    predict_req = PredictRequest(material_id=material_id,
                                 material=candidate.material,
                                 created_from_id=candidate.uid,
                                 identifiers=candidate.identifiers)

    session.set_response(candidate.dump())

    predict_response = design_execution.predict(predict_request=predict_req)
    assert session.num_calls == 1
    expected_call = FakeCall(
        method='POST',
        path=f"/projects/{design_execution.project_id}/design-workflows/{design_execution.workflow_id}"
             + f"/executions/{design_execution.uid}/predict",
        json={
            'material_id': str(material_id),
            'identifiers': [],
            'material': candidate.material.dump(),
            'created_from_id': str(candidate.uid),
            'random_seed': None
        },
        version="v1"
    )

    assert expected_call == session.last_call
    assert predict_response.dump() == candidate.dump()
