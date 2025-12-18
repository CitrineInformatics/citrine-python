from typing import List, Optional, Set

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._rest.resource import Resource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.predictors import PredictorNode

__all__ = ['AutoMLPredictor', 'AutoMLEstimator']


class AutoMLEstimator(BaseEnumeration):
    """[ALPHA] Algorithms to be used during AutoML model selection.

    * LINEAR corresponds to a linear regression estimator
        (valid for single-task regression problems)
    * RANDOM_FOREST corresponds to a random forest estimator
        (valid for single-task and multi-task regression and classification problems)
    * GAUSSIAN_PROCESS corresponds to a Gaussian process estimator
        (valid for single-task regression and classification problems)
    * SUPPORT_VECTOR_MACHINE corresponds to an support machine estimator
        (valid for single-task classification problems)
    * ALL combines all estimator choices (valid for all learning tasks)
    """

    LINEAR = "LINEAR"
    RANDOM_FOREST = "RANDOM_FOREST"
    GAUSSIAN_PROCESS = "GAUSSIAN_PROCESS"
    SUPPORT_VECTOR_MACHINE = "SUPPORT_VECTOR_MACHINE"
    ALL = "ALL"


class AutoMLPredictor(Resource["AutoMLPredictor"], PredictorNode):
    """A predictor interface that builds a single ML model.

    The model uses the set of inputs to predict the output(s).
    Only one machine learning model is built.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    inputs: list[Descriptor]
        Descriptors that represent inputs to the model
    outputs: list[Descriptor]
        Descriptors that represents the output(s) of the model.
    estimators: Optional[Set[AutoMLEstimator]]
        Set of estimators to consider during during AutoML model selection.
        If None is provided, defaults to AutoMLEstimator.RANDOM_FOREST.

    """

    inputs = _properties.List(_properties.Object(Descriptor), 'inputs')
    outputs = _properties.List(_properties.Object(Descriptor), 'outputs')
    estimators = _properties.Set(
        _properties.Enumeration(AutoMLEstimator),
        'estimators',
        default={AutoMLEstimator.RANDOM_FOREST}
    )

    typ = _properties.String('type', default='AutoML', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 outputs: List[Descriptor],
                 inputs: List[Descriptor],
                 estimators: Optional[Set[AutoMLEstimator]] = None):
        self.name: str = name
        self.description: str = description
        self.inputs: List[Descriptor] = inputs
        self.estimators: Set[AutoMLEstimator] = estimators or {AutoMLEstimator.RANDOM_FOREST}
        self.outputs = outputs

    def __str__(self):
        return '<AutoMLPredictor {!r}>'.format(self.name)
