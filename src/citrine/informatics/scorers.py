"""Tools for working with Scorers."""
from typing import List, Optional

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.constraints import Constraint
from citrine.informatics.objectives import Objective


class Scorer(PolymorphicSerializable['Scorer']):
    """A Citrine Scorer."""

    @classmethod
    def get_type(cls, data):
        """Return the sole currently implemented subtype."""
        return MLIScorer


class MLIScorer(Serializable['MLIScorer'], Scorer):
    """A Citrine MLIScorer."""

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
        return '<MLIScorer {!r}>'.format(self.name)
