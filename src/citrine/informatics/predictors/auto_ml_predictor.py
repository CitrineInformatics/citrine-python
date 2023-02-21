from typing import List, Optional, Set

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._rest.engine_resource import VersionedEngineResource
from citrine._serialization import properties as _properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.predictors import Predictor

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


class AutoMLPredictor(VersionedEngineResource['AutoMLPredictor'], Predictor):
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
        Currently, only one output Descriptor is supported.
    estimators: Optional[Set[AutoMLEstimator]]
        Set of estimators to consider during during AutoML model selection.
        If None is provided, defaults to AutoMLEstimator.RANDOM_FOREST.
    training_data: Optional[List[DataSource]]
        Sources of training data. Each can be either a CSV or an GEM Table. Candidates from
        multiple data sources will be combined into a flattened list and de-duplicated by uid and
        identifiers. De-duplication is performed if a uid or identifier is shared between two or
        more rows. The content of a de-duplicated row will contain the union of data across all
        rows that share the same uid or at least 1 identifier. Training data is unnecessary if the
        predictor is part of a graph that includes all training data required by this predictor.

    """

    inputs = _properties.List(_properties.Object(Descriptor), 'data.instance.inputs')
    outputs = _properties.List(_properties.Object(Descriptor), 'data.instance.outputs')
    estimators = _properties.Set(
        _properties.Enumeration(AutoMLEstimator),
        'data.instance.estimators',
        default={AutoMLEstimator.RANDOM_FOREST}
    )
    training_data = _properties.List(
        _properties.Object(DataSource),
        'data.instance.training_data',
        default=[]
    )

    typ = _properties.String('data.instance.type', default='AutoML', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 outputs: List[Descriptor],
                 inputs: List[Descriptor],
                 estimators: Optional[Set[AutoMLEstimator]] = None,
                 training_data: Optional[List[DataSource]] = None):
        self.name: str = name
        self.description: str = description
        self.inputs: List[Descriptor] = inputs
        self.estimators: Set[AutoMLEstimator] = estimators or {AutoMLEstimator.RANDOM_FOREST}
        self.training_data: List[DataSource] = training_data or []
        self.outputs = outputs

    def __str__(self):
        return '<AutoMLPredictor {!r}>'.format(self.name)
