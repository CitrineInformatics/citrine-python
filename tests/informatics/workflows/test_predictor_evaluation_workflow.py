import pytest

from citrine.informatics.predictor_evaluator import CrossValidationEvaluator
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


def test_dump(pew):
    assert pew.dump()["name"] == "Test"


def test_print(pew):
    assert "PredictorEvaluationWorkflow" in str(pew)


def test_execution_error(pew):
    with pytest.raises(AttributeError):
        pew.executions

    pew.project_id = "foo"
    assert pew.executions.project_id == "foo"
