"""Tools for working with Scores."""
import warnings
from typing import List, Optional

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.constraints import Constraint
from citrine.informatics.objectives import Objective

__all__ = ['Score', 'LIScore', 'EIScore', 'EVScore']


class Score(PolymorphicSerializable['Score']):
    """A Citrine Score is used to rank materials according to objectives and constraints.

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

    @property
    def name(self):
        """Getter for the score's name."""
        msg = "Getting the Score's name is deprecated."
        warnings.warn(msg, category=DeprecationWarning)
        return self._name

    @property
    def description(self):
        """Getter for the score's description."""
        msg = "Getting the Score's description is deprecated."
        warnings.warn(msg, category=DeprecationWarning)
        return self._description


class LIScore(Serializable['LIScore'], Score):
    """Evaluates the likelihood of scoring better than some baselines for given objectives.

    Parameters
    ----------
    objectives: list[Objective]
        objectives (e.g., maximize, minimize, tune, etc.)
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
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 objectives: List[Objective],
                 baselines: List[float],
                 constraints: Optional[List[Constraint]] = None,
                 session: Optional[Session] = None):
        self.objectives: List[Objective] = objectives
        self.baselines: List[float] = baselines
        self.constraints: List[Constraint] = constraints or []
        self.session: Optional[Session] = session

        if name is not None:
            msg = "Naming of Scores is deprecated.  Please do not define the name."
            warnings.warn(msg, category=DeprecationWarning)
            self._name = name
        else:
            self._name = "Likelihood of Improvement"

        if description is not None:
            msg = "Describing Scores is deprecated.  Please do not define the description."
            warnings.warn(msg, category=DeprecationWarning)
            self._description: str = description
        else:
            self._description = ""

    def __str__(self):
        return '<LIScore>'


class EIScore(Serializable['EIScore'], Score):
    """
    Evaluates the expected magnitude of improvement beyond baselines for given objectives.

    Parameters
    ----------
    objectives: list[Objective]
        objectives (e.g., maximize, minimize, tune, etc.)
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
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 objectives: List[Objective],
                 baselines: List[float],
                 constraints: Optional[List[Constraint]] = None,
                 session: Optional[Session] = None):
        self.objectives: List[Objective] = objectives
        self.baselines: List[float] = baselines
        self.constraints: List[Constraint] = constraints or []
        self.session: Optional[Session] = session

        if name is not None:
            msg = "Naming of Scores is deprecated.  Please do not define the name."
            warnings.warn(msg, category=DeprecationWarning)
            self._name = name
        else:
            self._name = "Expected Improvement"

        if description is not None:
            msg = "Describing Scores is deprecated.  Please do not define the description."
            warnings.warn(msg, category=DeprecationWarning)
            self._description: str = description
        else:
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
    constraints: list[Constraint]
        constraints limiting the allowed values that material instances can have

    """

    objectives = properties.List(properties.Object(Objective), 'objectives')
    constraints = properties.List(properties.Object(Constraint), 'constraints')
    typ = properties.String('type', default='MEV')

    def __init__(self, *,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 objectives: List[Objective],
                 constraints: Optional[List[Constraint]] = None,
                 session: Optional[Session] = None):
        self.objectives: List[Objective] = objectives
        self.constraints: List[Constraint] = constraints or []
        self.session: Optional[Session] = session

        if name is not None:
            msg = "Naming of Scores is deprecated.  Please do not define the name."
            warnings.warn(msg, category=DeprecationWarning)
            self._name = name
        else:
            self._name = "Expected Value"

        if description is not None:
            msg = "Describing Scores is deprecated.  Please do not define the description."
            warnings.warn(msg, category=DeprecationWarning)
            self._description: str = description
        else:
            self._description = ""

    def __str__(self):
        return '<EVScore>'
