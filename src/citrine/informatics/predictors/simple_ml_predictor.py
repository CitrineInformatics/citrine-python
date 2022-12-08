from typing import List, Optional
from warnings import warn

from citrine._rest.engine_resource import VersionedEngineResource
from citrine._serialization import properties as _properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.predictors import Predictor

__all__ = ['SimpleMLPredictor']


class SimpleMLPredictor(VersionedEngineResource['SimplePredictor'], Predictor):
    """[DEPRECATED] A predictor interface that builds a simple graphical model.

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
        multiple data sources will be combined into a flattened list and de-duplicated by uid and
        identifiers. de-duplication is performed if a uid or identifier is shared between two or
        more rows. The content of a de-duplicated row will contain the union of data across all
        rows that share the same uid or at least 1 identifier. Training data is unnecessary if the
        predictor is part of a graph that includes all training data required by this predictor.

    """

    inputs = _properties.List(_properties.Object(Descriptor), 'data.instance.inputs')
    outputs = _properties.List(_properties.Object(Descriptor), 'data.instance.outputs')
    latent_variables = _properties.List(_properties.Object(Descriptor),
                                        'data.instance.latent_variables')
    training_data = _properties.List(_properties.Object(DataSource),
                                     'data.instance.training_data', default=[])

    typ = _properties.String('data.instance.type', default='Simple', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 inputs: List[Descriptor],
                 outputs: List[Descriptor],
                 latent_variables: List[Descriptor],
                 training_data: Optional[List[DataSource]] = None):
        warn("SimpleMLPredictor is deprecated as of 1.29.0 and will be removed in 2.0.0."
             " Please use the builders.predictors.build_simple_ml.", category=DeprecationWarning)
        self.name: str = name
        self.description: str = description
        self.inputs: List[Descriptor] = inputs
        self.outputs: List[Descriptor] = outputs
        self.latent_variables: List[Descriptor] = latent_variables
        self.training_data: List[DataSource] = training_data or []

    def __str__(self):
        return '<SimplePredictor {!r}>'.format(self.name)
