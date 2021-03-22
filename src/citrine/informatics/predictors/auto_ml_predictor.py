from typing import List, Optional

from citrine._serialization import properties as _properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.reports import Report
from citrine.informatics.predictors import Predictor

__all__ = ['AutoMLPredictor']


class AutoMLPredictor(Serializable['AutoMLPredictor'], Predictor):
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
        multiple data sources will be combined into a flattened list and deduplicated by uid and
        identifiers. Deduplication is performed if a uid or identifier is shared between two or
        more rows. The content of a deduplicated row will contain the union of data across all rows
        that share the same uid or at least 1 identifier. Training data is unnecessary if the
        predictor is part of a graph that includes all training data required by this predictor.

    """

    inputs = _properties.List(_properties.Object(Descriptor), 'config.inputs')
    output = _properties.Object(Descriptor, 'output')
    training_data = _properties.List(_properties.Object(DataSource), 'config.training_data')
    typ = _properties.String('config.type', default='AutoML', deserializable=False)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 description: str,
                 output: Descriptor,
                 inputs: List[Descriptor],
                 training_data: Optional[List[DataSource]] = None,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 archived: bool = False):
        self.name: str = name
        self.description: str = description
        self.inputs: List[Descriptor] = inputs
        self.output: Descriptor = output
        self.training_data: List[DataSource] = self._wrap_training_data(training_data)
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.archived: bool = archived

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
