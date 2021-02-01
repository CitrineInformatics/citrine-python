from typing import List, Optional, Union
from uuid import UUID

from citrine._serialization import properties as _properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.data_sources import DataSource
from citrine.informatics.reports import Report
from citrine.informatics.predictors import Predictor

__all__ = ['GraphPredictor']


class GraphPredictor(Serializable['GraphPredictor'], Predictor):
    """A predictor interface that stitches other predictors together.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    predictors: List[Union[UUID, Predictor]]
        the list of predictors to use in the grpah, either UUIDs or serialized predictors
    training_data: Optional[List[DataSource]]
        Optional sources of training data shared by all predictors in the graph.
        Training data provided by this graph predictor does not need to be specified as part of the
        configuration of sub-predictors. Shared training data and any training data specified
        by a sub-predictor will be combined into a flattened list and deduplicated
        by uid and identifiers. Deduplication is performed if a uid or identifier is shared between
        two or more rows. The content of a deduplicated row will contain the union of data
        across all rows that share the same uid or at least 1 identifier.

    """

    predictors = _properties.List(_properties.Union(
        [_properties.UUID, _properties.Object(Predictor)]), 'config.predictors')
    # the default seems to be defined in instances, not the class itself
    # this is tested in test_graph_default_training_data
    training_data = _properties.List(
        _properties.Object(DataSource), 'config.training_data', default=[])
    typ = _properties.String('config.type', default='Graph', deserializable=False)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 description: str,
                 predictors: List[Union[UUID, Predictor]],
                 training_data: Optional[List[DataSource]] = None,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 archived: bool = False):
        self.name: str = name
        self.description: str = description
        self.predictors: List[Union[UUID, Predictor]] = predictors
        self.training_data: List[DataSource] = self._wrap_training_data(training_data)
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.archived: bool = archived

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
        """Insert a serialized embedded predictor into a module envelope, to facilitate deser."""
        return dict(
            module_type='PREDICTOR',
            config=predictor,
            archived=False
        )

    def __str__(self):
        return '<GraphPredictor {!r}>'.format(self.name)
