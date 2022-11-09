from typing import Dict, Type

from citrine._serialization.serializable import Serializable
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization import properties

__all__ = [
    'ExperimentValue',
    'RealExperimentValue',
    'IntegerExperimentValue',
    'CategoricalExperimentValue',
    'MixtureExperimentValue',
    'ChemicalFormulaExperimentValue',
    'MolecularStructureExperimentValue'
]


class ExperimentValue(PolymorphicSerializable['ExperimentValue']):
    """An container for experiment values.

    Abstract type that returns the proper type given a serialized dict.
    """

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        return {
            "RealValue": RealExperimentValue,
            "IntegerValue": IntegerExperimentValue,
            "CategoricalValue": CategoricalExperimentValue,
            "MixtureValue": MixtureExperimentValue,
            "OrganicValue": ChemicalFormulaExperimentValue,
            "InorganicValue": MolecularStructureExperimentValue,
        }[data["type"]]

    def __str__(self):
        return f"<{self.__class__.__name__} {self.value!r}>"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

    def __eq__(self, other):
        return self._equals(other, ["value", "typ"])

    def _equals(self, other, attrs) -> bool:
        """Check to see if the attrs from the other instance match this instance.

        Returns True if all of the attribute names from attrs match between this and
        the other instance, else False. A missing attribute from this instance will
        raise an AttributeError, and False if missing from the other instance.

        Parameters
        ----------
        other: Description
            the Description instance to compare to
        attrs: List[str]
            A list of attribute names to lookup and compare

        """
        # Check that all attrs exist on this object and raise an AttributeError if not.
        [self.__getattribute__(key) for key in attrs]

        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in attrs
            ])
        except AttributeError:
            return False


class RealExperimentValue(Serializable['RealExperimentValue'], ExperimentValue):
    """A floating point experiment result."""

    value = properties.Float('value')
    typ = properties.String('type', default='RealValue', deserializable=False)

    def __init__(self, value: float):
        self.value = value


class IntegerExperimentValue(Serializable['IntegerExperimentValue'], ExperimentValue):
    """An integer value experiment result."""

    value = properties.Integer('value')
    typ = properties.String('type', default='IntegerValue', deserializable=False)

    def __init__(self, value: int):
        self.value = value


class CategoricalExperimentValue(Serializable['CategoricalExperimentValue'], ExperimentValue):
    """An experiment result with a categorical value."""

    value = properties.String('value')
    typ = properties.String('type', default='CategoricalValue', deserializable=False)

    def __init__(self, value: str):
        self.value = value


class MixtureExperimentValue(Serializable['MixtureExperimentValue'], ExperimentValue):
    """An experiment result mapping ingredients and labels to real values."""

    value = properties.Mapping(properties.String, properties.Float, 'value')
    typ = properties.String('type', default='MixtureValue', deserializable=False)

    def __init__(self, value: Dict[str, float]):
        self.value = value


class ChemicalFormulaExperimentValue(Serializable['ChemicalFormulaExperimentValue'],
                                     ExperimentValue):
    """Experiment value for a chemical formula."""

    value = properties.String('value')
    typ = properties.String('type', default='OrganicValue', deserializable=False)

    def __init__(self, value: str):
        self.value = value


class MolecularStructureExperimentValue(Serializable['MolecularStructureExperimentValue'],
                                        ExperimentValue):
    """Experiment value for a molecular structure."""

    value = properties.String('value')
    typ = properties.String('type', default='InorganicValue', deserializable=False)

    def __init__(self, value: str):
        self.value = value
