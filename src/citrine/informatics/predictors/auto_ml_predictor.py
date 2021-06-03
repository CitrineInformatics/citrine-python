from typing import List, Optional

from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties as _properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.predictors import Predictor
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['AutoMLPredictor']


class AutoMLPredictor(Resource['AutoMLPredictor'], Predictor, AIResourceMetadata):
    """[ALPHA] A predictor interface that builds a single ML model.

    The model uses the set of inputs to predict the output.
    Only one value for output is currently supported.
    Only one machine learning model is built.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    inputs: list[Descriptor]
        Descriptors that represent inputs to the model
    output: Descriptor
        A single Descriptor that represents the output of the model
    training_data: Optional[List[DataSource]]
        Sources of training data. Each can be either a CSV or an GEM Table. Candidates from
        multiple data sources will be combined into a flattened list and de-duplicated by uid and
        identifiers. De-duplication is performed if a uid or identifier is shared between two or
        more rows. The content of a de-duplicated row will contain the union of data across all
        rows that share the same uid or at least 1 identifier. Training data is unnecessary if the
        predictor is part of a graph that includes all training data required by this predictor.

    """

    _resource_type = ResourceTypeEnum.MODULE

    inputs = _properties.List(_properties.Object(Descriptor), 'config.inputs')
    output = _properties.Object(Descriptor, 'output')
    training_data = _properties.List(_properties.Object(DataSource),
                                     'config.training_data', default=[])

    typ = _properties.String('config.type', default='AutoML', deserializable=False)
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 output: Descriptor,
                 inputs: List[Descriptor],
                 training_data: Optional[List[DataSource]] = None):
        self.name: str = name
        self.description: str = description
        self.inputs: List[Descriptor] = inputs
        self.output: Descriptor = output
        self.training_data: List[DataSource] = training_data or []

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        data['config']['outputs'] = [data['output']]
        data['config']['responses'] = [data['output']]
        return data

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        if 'outputs' in data['config']:
            data['output'] = data['config']['outputs'][0]
        elif 'responses' in data['config']:
            data['output'] = data['config']['responses'][0]
        return data

    def __str__(self):
        return '<AutoMLPredictor {!r}>'.format(self.name)
