import pytest
import uuid

from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.predictor_evaluator import HoldoutSetEvaluator, CrossValidationEvaluator, PredictorEvaluator
from citrine.informatics.workflows import PredictorEvaluationWorkflow


@pytest.fixture()
def pew():
    data_source = GemTableDataSource(table_id=uuid.uuid4(), table_version=3)
    evaluator1 = CrossValidationEvaluator(name="test CV", responses={"foo"})
    evaluator2 = HoldoutSetEvaluator(name="test holdout", responses={"foo"}, data_source=data_source)
    pew = PredictorEvaluationWorkflow(
        name="Test",
        description="TestWorkflow",
        evaluators=[evaluator1, evaluator2]
    )
    return pew


def test_round_robin(pew):
    dumped = pew.dump()
    assert dumped["name"] == "Test"
    assert dumped["description"] == "TestWorkflow"
    assert PredictorEvaluator.build(dumped["evaluators"][0]).name == pew.evaluators[0].name


def test_print(pew):
    assert "PredictorEvaluationWorkflow" in str(pew)


def test_execution_error(pew):
    with pytest.raises(AttributeError):
        pew.executions

    pew.project_id = "foo"
    assert pew.executions.project_id == "foo"
