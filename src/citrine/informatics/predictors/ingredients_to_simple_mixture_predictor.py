from typing import Set, Mapping
from warnings import warn

from citrine._rest.engine_resource import EngineResource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
from citrine.informatics.predictors import Predictor

__all__ = ['IngredientsToSimpleMixturePredictor']


class IngredientsToSimpleMixturePredictor(
        EngineResource['IngredientsToSimpleMixturePredictor'], Predictor):
    """[DEPRECATED] Constructs a simple mixture from ingredient quantities.

    This predictor has been renamed. Please use
    :class:`~citrine.informatics.predictors.ingredients_to_formulation_predictor.IngredientsToFormulationPredictor`
    instead.

    .. seealso::

        :class:`~citrine.informatics.predictors.ingredients_to_formulation_predictor.IngredientsToFormulationPredictor`

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    output: FormulationDescriptor
        descriptor that represents the output formulation
    id_to_quantity: Mapping[str, RealDescriptor]
        Map from ingredient identifier to the descriptor that represents its quantity,
        e.g., ``{'water': RealDescriptor('water quantity', 0, 1, "")}``
    labels: Mapping[str, Set[str]]
        Map from each label to all ingredients assigned that label, when present in a mixture
        e.g., ``{'solvent': {'water'}}``

    """

    output = _properties.Object(FormulationDescriptor, 'data.instance.output')
    id_to_quantity = _properties.Mapping(_properties.String, _properties.Object(RealDescriptor),
                                         'data.instance.id_to_quantity')
    labels = _properties.Mapping(_properties.String, _properties.Set(_properties.String),
                                 'data.instance.labels')

    typ = _properties.String('data.instance.type', default='IngredientsToSimpleMixture',
                             deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 output: FormulationDescriptor,
                 id_to_quantity: Mapping[str, RealDescriptor],
                 labels: Mapping[str, Set[str]]):
        warn("{this_class} has been renamed. Please use {replacement} instead"
             .format(this_class=self.__class__.__name__,
                     replacement="Ingredients To Formulation Predictor"),
             DeprecationWarning
             )
        self.name: str = name
        self.description: str = description
        self.output: FormulationDescriptor = output
        self.id_to_quantity: Mapping[str, RealDescriptor] = id_to_quantity
        self.labels: Mapping[str, Set[str]] = labels

    def __str__(self):
        return '<IngredientsToSimpleMixturePredictor {!r}>'.format(self.name)  # pragma: no cover
