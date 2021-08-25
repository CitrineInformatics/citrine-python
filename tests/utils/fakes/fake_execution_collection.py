from typing import Optional
from uuid import UUID

from citrine._session import Session
from citrine.informatics.executions import DesignExecution, PredictorEvaluationExecution
from citrine.informatics.scores import Score

from citrine.resources.design_execution import DesignExecutionCollection
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecutionCollection


class FakeDesignExecutionCollection(DesignExecutionCollection):

    def __init__(self, project_id: UUID, session: Session, workflow_id: Optional[UUID] = None):
        super().__init__(project_id, session, workflow_id)

    def trigger(self, execution_input: Score) -> DesignExecution:
        execution = DesignExecution()
        execution.score = execution_input
        execution.descriptors = []
        return execution


class FakePredictorEvaluationExecutionCollection(PredictorEvaluationExecutionCollection):

    def __init__(self, project_id: UUID, session: Session, workflow_id: Optional[UUID] = None):
        super().__init__(project_id, session, workflow_id)

    def trigger(self, predictor_id: UUID) -> PredictorEvaluationExecution:
        return PredictorEvaluationExecution()
