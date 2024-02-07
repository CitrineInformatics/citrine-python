from typing import List, Optional

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

    training_data = properties.List(properties.Object(DataSource), 'training_data', default=[])

    typ = properties.String('type', default='SimpleMixture', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 training_data: Optional[List[DataSource]] = None):
        self.name: str = name
        self.description: str = description
        self.training_data: List[DataSource] = training_data or []

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
