"""Tools for working with Scores."""
from typing import List, Optional

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.constraints import Constraint
from citrine.informatics.objectives import Objective

__all__ = ['Score', 'MLIScore', 'MEIScore']


class Score(PolymorphicSerializable['Score']):
    """A Citrine Score is used to rank materials according to objectives and constraints.

    Abstract type that returns the proper type given a serialized dict.


    """

    @classmethod
    def get_type(cls, data):
        """Return the subtype."""
        return {
            'MLI': MLIScore,
            'MEI': MEIScore
        }[data['type']]


class MLIScore(Serializable['MLIScore'], Score):
    """Evaluates the likelihood of scoring better than some baselines for given objectives.

    Parameters
    ----------
    name: str
        the name of the score
    description: str
        the description of the score
    objectives: list[Objective]
        objectives (e.g., maximize, minimize, tune, etc.)
    baselines: list[float]
        best-so-far values for the various objectives (there must be one for each objective)
    constraints: list[Constraint]
        constraints limiting the allowed values that material instances can have

    """

    name = properties.String('name')
    description = properties.String('description')
    baselines = properties.List(properties.Float, 'baselines')
    objectives = properties.List(properties.Object(Objective), 'objectives')
    constraints = properties.List(properties.Object(Constraint), 'constraints')
    typ = properties.String('type', default='MLI')

    def __init__(self,
                 name: str,
                 description: str,
                 objectives: List[Objective],
                 baselines: List[float],
                 constraints: Optional[List[Constraint]] = None,
                 session: Optional[Session] = None):
        self.name: str = name
        self.description: str = description
        self.objectives: List[Objective] = objectives
        self.baselines: List[float] = baselines
        self.constraints: List[Constraint] = constraints or []
        self.session: Optional[Session] = session

    def __str__(self):
        return '<MLIScore {!r}>'.format(self.name)


class MEIScore(Serializable['MEIScore'], Score):
    """Evaluates the expected magnitude of improvement beyond some baselines for given objectives.

    Parameters
    ----------
    name: str
        the name of the score
    description: str
        the description of the score
    objectives: list[Objective]
        objectives (e.g., maximize, minimize, tune, etc.)
    baselines: list[float]
        best-so-far values for the various objectives (there must be one for each objective)
    constraints: list[Constraint]
        constraints limiting the allowed values that material instances can have

    """

    name = properties.String('name')
    description = properties.String('description')
    baselines = properties.List(properties.Float, 'baselines')
    objectives = properties.List(properties.Object(Objective), 'objectives')
    constraints = properties.List(properties.Object(Constraint), 'constraints')
    typ = properties.String('type', default='MEI')

    def __init__(self,
                 name: str,
                 description: str,
                 objectives: List[Objective],
                 baselines: List[float],
                 constraints: Optional[List[Constraint]] = None,
                 session: Optional[Session] = None):
        self.name: str = name
        self.description: str = description
        self.objectives: List[Objective] = objectives
        self.baselines: List[float] = baselines
        self.constraints: List[Constraint] = constraints or []
        self.session: Optional[Session] = session

    def __str__(self):
        return '<MEIScore {!r}>'.format(self.name)
