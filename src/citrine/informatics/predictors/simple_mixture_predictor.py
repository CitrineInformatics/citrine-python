from citrine._rest.resource import Resource
from citrine._serialization import properties
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

    """

    typ = properties.String('type', default='SimpleMixture', deserializable=False)

    def __init__(self, name: str, *, description: str):
        self.name: str = name
        self.description: str = description

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
