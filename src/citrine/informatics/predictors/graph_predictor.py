from typing import List, Optional, Union
from uuid import UUID

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties as _properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.predictors import Predictor
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['GraphPredictor']


class GraphPredictor(Resource['GraphPredictor'], Predictor, AIResourceMetadata):
    """A predictor interface that stitches other predictors together.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    predictors: List[Union[UUID, Predictor]]
        the list of predictors to use in the graph, either UUIDs or serialized predictors
    training_data: Optional[List[DataSource]]
        Optional sources of training data shared by all predictors in the graph.
        Training data provided by this graph predictor does not need to be specified as part of the
        configuration of sub-predictors. Shared training data and any training data specified
        by a sub-predictor will be combined into a flattened list and de-duplicated
        by uid and identifiers. De-duplication is performed if a uid or identifier is shared
        between two or more rows. The content of a de-duplicated row will contain the union of
        data across all rows that share the same uid or at least 1 identifier.

    """

    _resource_type = ResourceTypeEnum.MODULE

    predictors = _properties.List(_properties.Union(
        [_properties.UUID, _properties.Object(Predictor)]), 'config.predictors')
    # the default seems to be defined in instances, not the class itself
    # this is tested in test_graph_default_training_data
    training_data = _properties.List(_properties.Object(DataSource),
                                     'config.training_data', default=[])

    typ = _properties.String('config.type', default='Graph', deserializable=False)
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 predictors: List[Union[UUID, Predictor]],
                 training_data: Optional[List[DataSource]] = None):
        self.name: str = name
        self.description: str = description
        self.predictors: List[Union[UUID, Predictor]] = predictors
        self.training_data: List[DataSource] = training_data or []

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        for i, predictor in enumerate(data['config']['predictors']):
            if isinstance(predictor, dict):
                # embedded predictors are not modules, so only serialize their config
                data['config']['predictors'][i] = predictor['config']
        return data

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        for i, predictor in enumerate(data['config']['predictors']):
            if isinstance(predictor, dict):
                data['config']['predictors'][i] = \
                    GraphPredictor.stuff_predictor_into_envelope(predictor)
        return data

    @staticmethod
    def stuff_predictor_into_envelope(predictor: dict) -> dict:
        """Insert a serialized embedded predictor into a module envelope.

        This facilitates deserialization.
        """
        return dict(
            module_type='PREDICTOR',
            config=predictor,
            archived=False
        )

    def __str__(self):
        return '<GraphPredictor {!r}>'.format(self.name)
