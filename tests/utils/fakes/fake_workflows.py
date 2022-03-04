from citrine.informatics.workflows import DesignWorkflow, PredictorEvaluationWorkflow

from tests.utils.fakes import FakeDesignExecutionCollection, FakePredictorEvaluationExecutionCollection


class FakeDesignWorkflow(DesignWorkflow):

    @property
    def design_executions(self) -> FakeDesignExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize execution without project reference!')
        return FakeDesignExecutionCollection(
            project_id=self.project_id, session=self._session, workflow_id=self.uid)


class FakePredictorEvaluationWorkflow(PredictorEvaluationWorkflow):

    @property
    def executions(self) -> FakePredictorEvaluationExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, 'project_id', None) is None:
            raise AttributeError('Cannot initialize execution without project reference!')
        return FakePredictorEvaluationExecutionCollection(
            project_id=self.project_id, session=self._session, workflow_id=self.uid)