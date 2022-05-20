import warnings
from typing import List, Optional

from citrine._rest.engine_resource import EngineResource
from citrine._serialization import properties as _properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.predictors import Predictor

__all__ = ['AutoMLPredictor']


class AutoMLPredictor(EngineResource['AutoMLPredictor'], Predictor):
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
    output: Descriptor
        [DEPRECATED] Please use ``outputs`` instead
        A single Descriptor that represents the output of the model
    outputs: list[Descriptor]
        Descriptors that represents the output(s) of the model.
        Currently, only one output Descriptor is supported.
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
    training_data = _properties.List(_properties.Object(DataSource),
                                     'data.instance.training_data', default=[])

    typ = _properties.String('data.instance.type', default='AutoML', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 output: Descriptor = None,
                 outputs: List[Descriptor] = None,
                 inputs: List[Descriptor],
                 training_data: Optional[List[DataSource]] = None):
        self.name: str = name
        self.description: str = description
        self.inputs: List[Descriptor] = inputs
        self.training_data: List[DataSource] = training_data or []

        if output is not None:
            msg = ('The "output" parameter is deprecated as of 1.24.0 and will be removed in '
                   '2.0.0. Please use the "outputs" field instead.')
            warnings.warn(msg, category=DeprecationWarning)
            if outputs is not None:
                raise ValueError('Found values for "outputs" and the deprecated "output". Please '
                                 'provide only "outputs".')

        self.outputs: List[Descriptor] = []
        if outputs is not None:
            self.outputs = outputs
        elif output is not None:
            self.outputs = [output]

    @property
    def output(self) -> Optional[Descriptor]:
        """[DEPRECATED] Get the first output descriptor."""
        msg = ('The "output" field is deprecated as of 1.24.0 and will be removed in 2.0.0. '
               'Please use the "outputs" field instead.')
        warnings.warn(msg, category=DeprecationWarning)
        return self.outputs[0] if self.outputs else None

    @output.setter
    def output(self, value):
        """[DEPRECATED] Set the output descriptor."""
        msg = ('The "output" field is deprecated as of 1.24.0 and will be removed in 2.0.0. '
               'Please use the "outputs" field instead.')
        warnings.warn(msg, category=DeprecationWarning)
        if not isinstance(value, Descriptor):
            # Mirroring the error emited by serialization.
            raise ValueError(f"{value} is not one of valid types: <class 'Descriptor'> for output")

        self.outputs = [value]

    def __str__(self):
        return '<AutoMLPredictor {!r}>'.format(self.name)
