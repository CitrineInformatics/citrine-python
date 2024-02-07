import warnings
from typing import Set, Optional, Tuple

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.constraints.constraint import Constraint
from citrine.informatics.descriptors import FormulationDescriptor

__all__ = ['IngredientRatioConstraint']


class IngredientRatioConstraint(Serializable['IngredientRatioConstraint'], Constraint):
    """A formulation constraint operating on the ratio of quantities of ingredients and a basis.

    Example: "6 to 7 parts ingredient A per 100 parts ingredient B" becomes

    .. code:: python

       IngredientRatioConstraint(min=6, max=7, ingredient=("A", 100), basis_ingredients=["B"])

    Parameters
    ----------
    formulation_descriptor: FormulationDescriptor
        descriptor to constrain
    min: float
        minimum value for the ratio
    max: float
        maximum value for the ratio
    ingredient: Optional[tuple[str, float]]
        multiplier for an ingredient in the numerator of the ratio
    label: Optional[tuple[str, float]]
        multiplier for a label in the numerator of the ratio
    basis_ingredients: Optional[Union[list[str], dict[str, float]]]
        the ingredients which should appear in the denominator of the ratio
    basis_labels: Optional[Union[list[str], dict[str, float]]]
        the labels which should appear in the denominator of the ratio

    """

    formulation_descriptor = properties.Object(FormulationDescriptor, 'formulation_descriptor')
    min = properties.Float('min')
    max = properties.Float('max')

    # The backend provides ingredients and labels as dictionaries, but presently only allows one
    # between them. To clarify customer interaction, we only allow a single one of each to be set.
    # Since our serde library doesn't allow extracting from a dict with unknown keys, we do it by
    # hiding the dictionaries and exposing properties.
    _ingredients = properties.Mapping(
        properties.String, properties.Float, 'ingredients', default={})
    _labels = properties.Mapping(properties.String, properties.Float, 'labels', default={})

    # The backend provides basis ingredients and basis labels as a dictionary from the key to a
    # multiplier. However, for ingredient ratio constraints, the multiplier in the denominator
    # should always be one, so we can't allow users to enter it. We need to use properties for this
    # behavior. It also allows us to display deprecation warnings for the coming type change.
    _basis_ingredients = properties.Mapping(
        properties.String, properties.Float, 'basis_ingredients', default={})
    _basis_labels = properties.Mapping(
        properties.String, properties.Float, 'basis_labels', default={})

    typ = properties.String('type', default='IngredientRatio')

    def __init__(self, *,
                 formulation_descriptor: FormulationDescriptor,
                 min: float,
                 max: float,
                 ingredient: Optional[Tuple[str, float]] = None,
                 label: Optional[Tuple[str, float]] = None,
                 basis_ingredients: Set[str] = set(),
                 basis_labels: Set[str] = set()):
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

    @property
    def basis_ingredients(self) -> Set[str]:
        """Retrieve the ingredients in the denominator of the ratio."""
        return set(self._basis_ingredients.keys())

    @basis_ingredients.setter
    def basis_ingredients(self, value: Set[str]):
        """Set the ingredients in the denominator of the ratio."""
        self._basis_ingredients = dict.fromkeys(value, 1)

    @property
    def basis_ingredient_names(self) -> Set[str]:
        """Retrieve the names of all ingredients in the denominator of the ratio."""
        warnings.warn("basis_ingredient_names is deprecated as of 3.0.0 and will be dropped in "
                      "4.0. Please use basis_ingredients instead.", DeprecationWarning)
        return self.basis_ingredients

    # This is for symmetry; it's not strictly necessary.
    @basis_ingredient_names.setter
    def basis_ingredient_names(self, value: Set[str]):
        """Set the names of all ingredients in the denominator of the ratio."""
        warnings.warn("basis_ingredient_names is deprecated as of 3.0.0 and will be dropped in "
                      "4.0. Please use basis_ingredients instead.", DeprecationWarning)
        self.basis_ingredients = value

    @property
    def basis_labels(self) -> Set[str]:
        """Retrieve the labels in the denominator of the ratio."""
        return set(self._basis_labels.keys())

    @basis_labels.setter
    def basis_labels(self, value: Set[str]):
        """Set the labels in the denominator of the ratio."""
        self._basis_labels = dict.fromkeys(value, 1)

    @property
    def basis_label_names(self) -> Set[str]:
        """Retrieve the names of all labels in the denominator of the ratio."""
        warnings.warn("basis_label_names is deprecated as of 3.0.0 and will be dropped in 4.0. "
                      "Please use basis_labels instead.", DeprecationWarning)
        return self.basis_labels

    # This is for symmetry; it's not strictly necessary.
    @basis_label_names.setter
    def basis_label_names(self, value: Set[str]):
        """Set the names of all labels in the denominator of the ratio."""
        warnings.warn("basis_label_names is deprecated as of 3.0.0 and will be dropped in 4.0. "
                      "Please use basis_labels instead.", DeprecationWarning)
        self.basis_labels = value

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
        return f"<IngredientRatioConstraint '{self.formulation_descriptor.key}'>"
