from uuid import UUID

from citrine.informatics.executions import DesignExecution, PredictorEvaluationExecution
from citrine.informatics.scores import Score

from citrine.resources.design_execution import DesignExecutionCollection
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecutionCollection


class FakeDesignExecutionCollection(DesignExecutionCollection):

    def trigger(self, execution_input: Score) -> DesignExecution:
        execution = DesignExecution()
        execution.score = execution_input
        execution.descriptors = []
        return execution


class FakePredictorEvaluationExecutionCollection(PredictorEvaluationExecutionCollection):

    def trigger(self, predictor_id: UUID) -> PredictorEvaluationExecution:
        return PredictorEvaluationExecution()
