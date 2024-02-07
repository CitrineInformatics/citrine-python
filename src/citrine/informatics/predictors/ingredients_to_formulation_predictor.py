from typing import Set, Mapping

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
from citrine.informatics.predictors import PredictorNode

__all__ = ['IngredientsToFormulationPredictor']


class IngredientsToFormulationPredictor(
    Resource["IngredientsToFormulationPredictor"], PredictorNode
):
    """A predictor interface that constructs a formulation from ingredient quantities.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    id_to_quantity: Mapping[str, RealDescriptor]
        Map from ingredient identifier to the descriptor that represents its quantity,
        e.g., ``{'water': RealDescriptor('water quantity', 0, 1, "")}``
    labels: Mapping[str, Set[str]]
        Map from each label to all ingredients assigned that label, when present in a mixture,
        e.g., ``{'solvent': {'water'}}``

    """

    id_to_quantity = properties.Mapping(
        properties.String, properties.Object(RealDescriptor), 'id_to_quantity'
    )
    labels = properties.Mapping(properties.String, properties.Set(properties.String), 'labels')

    typ = properties.String('type', default='IngredientsToSimpleMixture', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 id_to_quantity: Mapping[str, RealDescriptor],
                 labels: Mapping[str, Set[str]]):
        self.name: str = name
        self.description: str = description
        self.id_to_quantity: Mapping[str, RealDescriptor] = id_to_quantity
        self.labels: Mapping[str, Set[str]] = labels

    def __str__(self):
        return '<IngredientsToFormulationPredictor {!r}>'.format(self.name)

    @property
    def output(self) -> FormulationDescriptor:
        """The output formulation descriptor with key 'Formulation'."""
        return FormulationDescriptor.hierarchical()
