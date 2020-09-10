from citrine.informatics.predictor_evaluator import PredictorEvaluator


class PredictorEvaluationResult:
    pass

    def evaluator(self) -> PredictorEvaluator:
        raise NotImplementedError()
