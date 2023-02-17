"""Tools for working with Scores."""
from typing import List, Optional

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.constraints import Constraint
from citrine.informatics.objectives import Objective

__all__ = ['Score', 'LIScore', 'EIScore', 'EVScore']


class Score(PolymorphicSerializable['Score']):
    """A Score is used to rank materials according to objectives and constraints.

    Abstract type that returns the proper type given a serialized dict.

    """

    _name = properties.String('name')
    _description = properties.String('description')

    @classmethod
    def get_type(cls, data):
        """Return the subtype."""
        return {
            'MLI': LIScore,
            'MEI': EIScore,
            'MEV': EVScore
        }[data['type']]


class LIScore(Serializable['LIScore'], Score):
    """Evaluates the likelihood of scoring better than some baselines for given objectives.

    Parameters
    ----------
    objectives: list[Objective]
        objectives (e.g., maximize, minimize, tune, etc.)
        If multiple objectives are specified then this score evaluates the likelihood of
        simultaneously exceeding all objectives.
    baselines: list[float]
        best-so-far values for the various objectives (there must be one for each objective)
    constraints: list[Constraint]
        constraints limiting the allowed values that material instances can have

    """

    baselines = properties.List(properties.Float, 'baselines')
    objectives = properties.List(properties.Object(Objective), 'objectives')
    constraints = properties.List(properties.Object(Constraint), 'constraints')
    typ = properties.String('type', default='MLI')

    def __init__(self, *,
                 objectives: List[Objective],
                 baselines: List[float],
                 constraints: Optional[List[Constraint]] = None):
        self.objectives: List[Objective] = objectives
        self.baselines: List[float] = baselines
        self.constraints: List[Constraint] = constraints or []
        self._name = "Likelihood of Improvement"
        self._description = ""

    def __str__(self):
        return '<LIScore>'


class EIScore(Serializable['EIScore'], Score):
    """
    Evaluates the expected magnitude of improvement beyond baselines for a given objective.

    Parameters
    ----------
    objectives: list[Objective]
        objectives (e.g., maximize, minimize, tune, etc.)
        EIScore does not support more than 1 objective at this time.
    baselines: list[float]
        best-so-far values for the various objectives (there must be one for each objective)
    constraints: list[Constraint]
        constraints limiting the allowed values that material instances can have

    """

    baselines = properties.List(properties.Float, 'baselines')
    objectives = properties.List(properties.Object(Objective), 'objectives')
    constraints = properties.List(properties.Object(Constraint), 'constraints')
    typ = properties.String('type', default='MEI')

    def __init__(self, *,
                 objectives: List[Objective],
                 baselines: List[float],
                 constraints: Optional[List[Constraint]] = None):
        self.objectives: List[Objective] = objectives
        self.baselines: List[float] = baselines
        self.constraints: List[Constraint] = constraints or []
        self._name = "Expected Improvement"
        self._description = ""

    def __str__(self):
        return '<EIScore>'


class EVScore(Serializable['EVScore'], Score):
    """
    Evaluates the expected value for given objectives.

    Parameters
    ----------
    objectives: list[Objective]
        objectives (e.g., maximize, minimize, tune, etc.)
        If multiple objectives are specified, their scores are summed together. This allows
        for simultaneous optimization of multiple objectives, although the weighting of the
        various objectives cannot be directly specified.
    constraints: list[Constraint]
        constraints limiting the allowed values that material instances can have

    """

    objectives = properties.List(properties.Object(Objective), 'objectives')
    constraints = properties.List(properties.Object(Constraint), 'constraints')
    typ = properties.String('type', default='MEV')

    def __init__(self, *,
                 objectives: List[Objective],
                 constraints: Optional[List[Constraint]] = None):
        self.objectives: List[Objective] = objectives
        self.constraints: List[Constraint] = constraints or []
        self._name = "Expected Value"
        self._description = ""

    def __str__(self):
        return '<EVScore>'
