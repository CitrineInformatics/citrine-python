from typing import Set

from citrine.informatics.predictor_evaluation_metrics import PredictorEvaluationMetric


class PredictorEvaluator:
    def responses(self) -> Set[str]:
        raise NotImplementedError

    def metrics(self) -> Set[PredictorEvaluationMetric]:
        raise NotImplementedError
