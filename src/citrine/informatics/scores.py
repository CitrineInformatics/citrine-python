"""Scores rank candidate materials during design executions.

A score combines one or more :class:`~citrine.informatics.objectives.Objective`
instances with optional :class:`~citrine.informatics.constraints.Constraint`
instances. The platform evaluates each candidate against the score and
returns candidates ranked from best to worst.

Three score types are available:

* :class:`LIScore` (Likelihood of Improvement) — multi-objective
  sequential optimization. Requires baseline values.
* :class:`EIScore` (Expected Improvement) — single-objective
  sequential optimization. Requires baseline values.
* :class:`EVScore` (Expected Value) — multi-objective sum of
  predicted values. No baselines needed.

"""
from typing import List, Optional

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.constraints import Constraint
from citrine.informatics.objectives import Objective

__all__ = ['Score', 'LIScore', 'EIScore', 'EVScore']


class Score(PolymorphicSerializable['Score']):
    """Base class for scoring strategies used in design executions.

    A Score ranks candidate materials by combining objectives
    (what to optimize) with constraints (what limits to respect).
    Use one of the concrete subclasses: :class:`LIScore`,
    :class:`EIScore`, or :class:`EVScore`.

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
    """Likelihood of Improvement — multi-objective sequential optimization.

    Ranks candidates by the probability that they simultaneously
    improve on *every* baseline. Best for iterative experimental
    campaigns where you want to beat your current best results
    across all objectives at once.

    Parameters
    ----------
    objectives : list[Objective]
        One or more objectives (e.g. ScalarMaxObjective,
        ScalarMinObjective). Multiple objectives are treated
        as a joint requirement: the score is the probability
        of exceeding *all* baselines simultaneously.
    baselines : list[float]
        Current best-known value for each objective, in the
        same order as ``objectives``. One baseline per
        objective is required.
    constraints : list[Constraint], optional
        Constraints that candidates must satisfy. Candidates
        violating any constraint receive a score of zero.

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
    """Expected Improvement — single-objective sequential optimization.

    Ranks candidates by the expected magnitude of improvement
    beyond the baseline. Unlike LIScore, this considers *how
    much* better a candidate is, not just the probability of
    being better. Best for single-objective campaigns where
    you want the largest possible gains.

    Parameters
    ----------
    objectives : list[Objective]
        Exactly one objective. EIScore does not support
        multiple objectives; use LIScore for multi-objective
        optimization.
    baselines : list[float]
        Current best-known value for the objective. Must
        contain exactly one value matching the single
        objective.
    constraints : list[Constraint], optional
        Constraints that candidates must satisfy. Candidates
        violating any constraint receive a score of zero.

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
    """Expected Value — multi-objective optimization without baselines.

    Ranks candidates by the sum of predicted values across all
    objectives. Unlike LIScore and EIScore, no baselines are
    needed. Useful as a starting point when you have no
    existing experimental results.

    When multiple objectives are specified, their individual
    scores are summed with equal weight. The relative
    weighting cannot be controlled directly; instead, adjust
    the descriptor scales or units to influence the balance.

    Parameters
    ----------
    objectives : list[Objective]
        One or more objectives. Scores are summed across all
        objectives.
    constraints : list[Constraint], optional
        Constraints that candidates must satisfy. Candidates
        violating any constraint receive a score of zero.

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
