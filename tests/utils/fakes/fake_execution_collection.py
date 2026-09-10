from citrine.informatics.executions import DesignExecution
from citrine.informatics.scores import Score
from citrine.resources.design_execution import DesignExecutionCollection


class FakeDesignExecutionCollection(DesignExecutionCollection):
    def trigger(
        self, execution_input: Score, max_candidates: int | None = None
    ) -> DesignExecution:
        execution = DesignExecution()
        execution.score = execution_input
        execution.descriptors = []
        return execution
