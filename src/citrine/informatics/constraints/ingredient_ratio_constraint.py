from typing import Mapping, Optional, Tuple

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.constraints.constraint import Constraint
from citrine.informatics.descriptors import FormulationDescriptor

__all__ = ['IngredientRatioConstraint']


class IngredientRatioConstraint(Serializable['IngredientRatioConstraint'], Constraint):
    """A formulation constraint operating on the ratio of quantities of ingredients and a basis.

    Parameters
    ----------
    formulation_descriptor: FormulationDescriptor
        descriptor to constrain
    min: float
        minimum value
    max: float
        maximum value
    ingredient: Optional[tuple[str, float]]
        multiplier for an ingredient in the numerator of the ratio
    label: Optional[tuple[str, float]]
        multiplier for a label in the numerator of the ratio
    basis_ingredients: Optional[dict[str, float]]
        map from ingredient to multiplier in the denominator of the ratio
    basis_labels: Optional[dict[str, float]]
        map from label to multiplier in the denominator of the ratio

    """

    formulation_descriptor = properties.Object(FormulationDescriptor, 'formulation_descriptor')
    min = properties.Float('min')
    max = properties.Float('max')
    basis_ingredients = properties.Mapping(
        properties.String, properties.Float, 'basis_ingredients', default={})
    basis_labels = properties.Mapping(
        properties.String, properties.Float, 'basis_labels', default={})

    # The backend provides ingredients and labels as dictionaries, but presently only allows one
    # between them. To clarify customer interaction, we only allow a single one of each to be set.
    # Since our serde library doesn't allow extracting from a dict with unknown keys, we do it by
    # hiding the dictionaries and exposing properties.
    _ingredients = properties.Mapping(
        properties.String, properties.Float, 'ingredients', default={})
    _labels = properties.Mapping(properties.String, properties.Float, 'labels', default={})

    typ = properties.String('type', default='IngredientRatio')

    def __init__(self, *,
                 formulation_descriptor: FormulationDescriptor,
                 min: float,
                 max: float,
                 ingredient: Optional[Tuple[str, float]] = None,
                 label: Optional[Tuple[str, float]] = None,
                 basis_ingredients: Mapping[str, float] = {},
                 basis_labels: Mapping[str, float] = {}):
        self.formulation_descriptor = formulation_descriptor
        self.min = min
        self.max = max
        self.ingredient = ingredient
        self.label = label
        self.basis_ingredients = basis_ingredients
        self.basis_labels = basis_labels

    @property
    def ingredient(self):
        """Retrieve the ingredient and its multiplier from the numerator, if it's been set."""
        return self._numerator_read(self._ingredients)

    @ingredient.setter
    def ingredient(self, value: Optional[Tuple[str, float]]):
        """Set the ingredient and its multiplier in the numerator."""
        self._ingredients = self._numerator_validate(value, "Ingredient")

    @property
    def label(self):
        """Retrieve the label and its multiplier from the numerator, if it's been set."""
        return self._numerator_read(self._labels)

    @label.setter
    def label(self, value: Optional[Tuple[str, float]]):
        """Set the label and its multiplier in the numerator."""
        self._labels = self._numerator_validate(value, "Label")

    def _numerator_read(self, num_dict):
        if num_dict:
            return tuple(num_dict.items())[0]
        else:
            return None

    def _numerator_validate(self, value, input_type):
        if value:
            if len(value) != 2:
                raise ValueError(f"{input_type} must be a name and a multiplier.")

            name, mult = value
            if mult <= 0.0:
                raise ValueError(f"{input_type} multipler must be greater than 0.")

            return {name: mult}
        else:
            return {}

    def __str__(self):
        return f'<IngredientRatioConstraint {self.formulation_descriptor.key!r}>'
