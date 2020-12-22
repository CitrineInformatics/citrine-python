from typing import List, Optional

from citrine._serialization import properties as _properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.reports import Report
from citrine.informatics.predictors import Predictor

__all__ = ['SimpleMLPredictor']


class SimpleMLPredictor(Serializable['SimplePredictor'], Predictor):
    """A predictor interface that builds a simple graphical model.

    The model connects the set of inputs through latent variables to the outputs.
    Supported complex inputs (such as chemical formulas) are auto-featurized and machine learning
    models are built for each latent variable and output.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    inputs: list[Descriptor]
        Descriptors that represent inputs to relations
    outputs: list[Descriptor]
        Descriptors that represent outputs of relations
    latent_variables: list[Descriptor]
        Descriptors that are predicted from inputs and used when predicting the outputs
    training_data: Optional[List[DataSource]]
        Sources of training data. Each can be either a CSV or an GEM Table. Candidates from
        multiple data sources will be combined into a flattened list and deduplicated by uid and
        identifiers. Deduplication is performed if a uid or identifier is shared between two or
        more rows. The content of a deduplicated row will contain the union of data across all rows
        that share the same uid or at least 1 identifier. Training data is unnecessary if the
        predictor is part of a graph that includes all training data required by this predictor.

    """

    inputs = _properties.List(_properties.Object(Descriptor), 'config.inputs')
    outputs = _properties.List(_properties.Object(Descriptor), 'config.outputs')
    latent_variables = _properties.List(_properties.Object(Descriptor), 'config.latent_variables')
    training_data = _properties.List(_properties.Object(DataSource), 'config.training_data')
    typ = _properties.String('config.type', default='Simple', deserializable=False)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 description: str,
                 inputs: List[Descriptor],
                 outputs: List[Descriptor],
                 latent_variables: List[Descriptor],
                 training_data: Optional[List[DataSource]] = None,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 archived: bool = False):
        self.name: str = name
        self.description: str = description
        self.inputs: List[Descriptor] = inputs
        self.outputs: List[Descriptor] = outputs
        self.latent_variables: List[Descriptor] = latent_variables
        self.training_data: List[DataSource] = self._wrap_training_data(training_data)
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.archived: bool = archived

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<SimplePredictor {!r}>'.format(self.name)
