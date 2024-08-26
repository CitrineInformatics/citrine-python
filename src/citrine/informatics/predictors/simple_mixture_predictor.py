from typing import List, Optional

from deprecation import deprecated

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.predictors import PredictorNode

__all__ = ['SimpleMixturePredictor']


class SimpleMixturePredictor(Resource["SimpleMixturePredictor"], PredictorNode):
    """A predictor interface that flattens a formulation into a simple mixture.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    training_data: Optional[List[DataSource]]
        Sources of training data. Each can be either a CSV or an GEM Table. Candidates from
        multiple data sources will be combined into a flattened list and de-duplicated by uid and
        identifiers. De-duplication is performed if a uid or identifier is shared between two or
        more rows. The content of a de-duplicated row will contain the union of data across all
        rows that share the same uid or at least 1 identifier. Training data is unnecessary if the
        predictor is part of a graph that includes all training data required by this predictor.

    """

    _training_data = properties.List(properties.Object(DataSource), 'training_data', default=[])

    typ = properties.String('type', default='SimpleMixture', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 training_data: Optional[List[DataSource]] = None):
        self.name: str = name
        self.description: str = description
        if training_data:
            self.training_data: List[DataSource] = training_data

    def __str__(self):
        return '<SimpleMixturePredictor {!r}>'.format(self.name)

    @property
    def input_descriptor(self) -> FormulationDescriptor:
        """The input formulation descriptor with key 'Formulation'."""
        return FormulationDescriptor.hierarchical()

    @property
    def output_descriptor(self) -> FormulationDescriptor:
        """The output formulation descriptor with key 'Flat Formulation'."""
        return FormulationDescriptor.flat()

    @property
    @deprecated(deprecated_in="3.5.0", removed_in="4.0.0",
                details="Training data must be accessed through the top-level GraphPredictor.'")
    def training_data(self):
        """[DEPRECATED] Retrieve training data associated with this node."""
        return self._training_data

    @training_data.setter
    @deprecated(deprecated_in="3.5.0", removed_in="4.0.0",
                details="Training data should only be added to the top-level GraphPredictor.'")
    def training_data(self, value):
        self._training_data = value
