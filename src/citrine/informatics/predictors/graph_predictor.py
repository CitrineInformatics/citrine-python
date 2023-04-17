from typing import List, Optional, Union
from uuid import UUID

from citrine._rest.engine_resource import VersionedEngineResource
from citrine._serialization import properties as properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.predictors import Predictor, PredictorNode

__all__ = ['GraphPredictor']


class GraphPredictor(VersionedEngineResource['GraphPredictor'], Predictor):
    """A predictor interface that stitches other predictors together.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    predictors: List[PredictorNode]
        the list of individual predictors to use in the graph
    training_data: Optional[List[DataSource]]
        Optional sources of training data shared by all predictors in the graph.
        Training data provided by this graph predictor does not need to be specified as part of the
        configuration of sub-predictors. Shared training data and any training data specified
        by a sub-predictor will be combined into a flattened list and de-duplicated
        by uid and identifiers. De-duplication is performed if a uid or identifier is shared
        between two or more rows. The content of a de-duplicated row will contain the union of
        data across all rows that share the same uid or at least 1 identifier.

    """

    predictors = properties.List(properties.Object(PredictorNode), 'data.instance.predictors')

    # the default seems to be defined in instances, not the class itself
    # this is tested in test_graph_default_training_data
    training_data = properties.List(
        properties.Object(DataSource), 'data.instance.training_data', default=[]
    )

    typ = properties.String('data.instance.type', default='Graph', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 predictors: List[PredictorNode],
                 training_data: Optional[List[DataSource]] = None):
        self.name: str = name
        self.description: str = description
        self.predictors: List[PredictorNode] = predictors
        self.training_data: List[DataSource] = training_data or []

    def __str__(self):
        return '<GraphPredictor {!r}>'.format(self.name)
