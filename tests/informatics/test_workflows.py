"""Tests for citrine.informatics.workflows."""
import json

import mock
from uuid import uuid4, UUID

import pytest

from citrine.informatics.design_candidate import DesignMaterial, DesignVariable, DesignCandidate, ChemicalFormula, \
    MeanAndStd, TopCategories, Mixture, MolecularStructure
from citrine.informatics.executions import DesignExecution
from citrine.informatics.predict_request import PredictRequest
from citrine.resources.design_workflow import DesignWorkflowCollection
from citrine._session import Session
from citrine.informatics.workflows import DesignWorkflow, Workflow
from citrine.resources.design_execution import DesignExecutionCollection
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def collection() -> DesignWorkflowCollection:
    return DesignWorkflowCollection(
        project_id=uuid4(),
        session=FakeSession(),
    )


@pytest.fixture
def execution_collection() -> DesignExecutionCollection:
    return DesignExecutionCollection(
        project_id=uuid4(),
        session=FakeSession(),
    )


PROJECT_ID = uuid4()

@pytest.fixture
def design_workflow(collection, design_workflow_dict) -> DesignWorkflow:
    return collection.build(design_workflow_dict)

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
            'material': {
                'vars': {
                    'Temperature': {
                        'm': 475.8,
                        "s": 0.0,
                        "type": "R"
                    },
                    "Flour": {
                        "cp": {
                                "flour": 100.0
                            },
                        "type": "C"
                    },
                    "Water": {
                        "q": {
                            "water": 72.5
                        },
                        "l": {},
                        "type": "M"
                    },
                    "Salt": {
                        "f": "NaCl",
                        "type": "F"
                    },
                    "Yeast": {
                        "s": "O1C=2C=C(C=3SC=C4C=CNC43)CC2C=5C=CC=6C=CNC6C15",
                        "type": "S"
                    }
                }
            },
            'created_from_id': str(candidate.uid),
            'random_seed': None
        },
        version="v1"
    )

    assert expected_call == session.last_call
    assert predict_response.dump() == candidate.dump()
