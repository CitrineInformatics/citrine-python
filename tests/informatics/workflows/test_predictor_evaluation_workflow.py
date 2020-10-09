import pytest

from citrine.informatics.predictor_evaluator import CrossValidationEvaluator, PredictorEvaluator
from citrine.informatics.workflows import PredictorEvaluationWorkflow


@pytest.fixture()
def pew():
    evaluator = CrossValidationEvaluator(name="test", responses={"foo"})
    pew = PredictorEvaluationWorkflow(
        name="Test",
        description="TestWorkflow",
        evaluators=[evaluator]
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
