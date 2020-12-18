from citrine._serialization import properties
from citrine._serialization.serializable import Serializable


__all__ = ['DesignCandidate']


class DesignCandidate(Serializable["DesignCandidate"]):
    """A Citrine Predictor Evaluation Result.

    This class represents a set of metrics computed by a Predictor Evaluator.
    """

    material_id = properties.UUID('material_id')
    identifiers = properties.List(properties.String(), 'identifiers')
    primary_score = properties.Float('primary_score')
    # material = ???

    def __init__(self):
        pass  # pragma: no cover
