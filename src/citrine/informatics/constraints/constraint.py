"""Tools for working with Constraints."""

from citrine._serialization.polymorphic_serializable import PolymorphicSerializable

__all__ = ['Constraint']


class Constraint(PolymorphicSerializable['Constraint']):
    """[ALPHA] A Citrine Constraint places restrictions on a design space.

    Abstract type that returns the proper type given a serialized dict.

    """

    _response_key = None

    @classmethod
    def get_type(cls, data):
        """Return the subtype."""
        from .categorical_constraint import CategoricalConstraint
        from .ingredient_count_constraint import IngredientCountConstraint
        from .ingredient_fraction_constraint import IngredientFractionConstraint
        from .label_fraction_constraint import LabelFractionConstraint
        from .scalar_range_constraint import ScalarRangeConstraint
        return {
            'Categorical': CategoricalConstraint,  # Kept for backwards compatibility.
            'AcceptableCategoriesConstraint': CategoricalConstraint,
            'IngredientCountConstraint': IngredientCountConstraint,
            'IngredientFractionConstraint': IngredientFractionConstraint,
            'LabelFractionConstraint': LabelFractionConstraint,
            'ScalarRange': ScalarRangeConstraint,
        }[data['type']]
