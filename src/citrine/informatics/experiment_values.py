from deprecation import deprecated

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
    """[DEPRECATED] An container for experiment values.

    Abstract type that returns the proper type given a serialized dict.
    """

    @classmethod
    @deprecated(deprecated_in="4.1.0", removed_in="5.0.0",
                details="Replaced by creating materials from candidates.")
    def build(cls, data: dict) -> 'ExperimentValue':
        """Build the underlying type."""
        return super().build(data)

    @classmethod
    def get_type(cls, data) -> type[Serializable]:
        """Return the subtype."""
        return {
            "RealValue": RealExperimentValue,
            "IntegerValue": IntegerExperimentValue,
            "CategoricalValue": CategoricalExperimentValue,
            "MixtureValue": MixtureExperimentValue,
            "InorganicValue": ChemicalFormulaExperimentValue,
            "OrganicValue": MolecularStructureExperimentValue,
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
        attrs: list[str]
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
    """[DEPRECATED] A floating point experiment result."""

    value = properties.Float('value')
    typ = properties.String('type', default='RealValue', deserializable=False)

    @deprecated(deprecated_in="4.1.0", removed_in="5.0.0",
                details="Replaced by creating materials from candidates.")
    def __init__(self, value: float):
        self.value = value


class IntegerExperimentValue(Serializable['IntegerExperimentValue'], ExperimentValue):
    """[DEPRECATED] An integer value experiment result."""

    value = properties.Integer('value')
    typ = properties.String('type', default='IntegerValue', deserializable=False)

    @deprecated(deprecated_in="4.1.0", removed_in="5.0.0",
                details="Replaced by creating materials from candidates.")
    def __init__(self, value: int):
        self.value = value


class CategoricalExperimentValue(Serializable['CategoricalExperimentValue'], ExperimentValue):
    """[DEPRECATED] An experiment result with a categorical value."""

    value = properties.String('value')
    typ = properties.String('type', default='CategoricalValue', deserializable=False)

    @deprecated(deprecated_in="4.1.0", removed_in="5.0.0",
                details="Replaced by creating materials from candidates.")
    def __init__(self, value: str):
        self.value = value


class MixtureExperimentValue(Serializable['MixtureExperimentValue'], ExperimentValue):
    """[DEPRECATED] An experiment result mapping ingredients and labels to real values."""

    value = properties.Mapping(properties.String, properties.Float, 'value')
    typ = properties.String('type', default='MixtureValue', deserializable=False)

    @deprecated(deprecated_in="4.1.0", removed_in="5.0.0",
                details="Replaced by creating materials from candidates.")
    def __init__(self, value: dict[str, float]):
        self.value = value


class ChemicalFormulaExperimentValue(Serializable['ChemicalFormulaExperimentValue'],
                                     ExperimentValue):
    """[DEPRECATED] Experiment value for a chemical formula."""

    value = properties.String('value')
    typ = properties.String('type', default='InorganicValue', deserializable=False)

    @deprecated(deprecated_in="4.1.0", removed_in="5.0.0",
                details="Replaced by creating materials from candidates.")
    def __init__(self, value: str):
        self.value = value


class MolecularStructureExperimentValue(Serializable['MolecularStructureExperimentValue'],
                                        ExperimentValue):
    """[DEPRECATED] Experiment value for a molecular structure."""

    value = properties.String('value')
    typ = properties.String('type', default='OrganicValue', deserializable=False)

    @deprecated(deprecated_in="4.1.0", removed_in="5.0.0",
                details="Replaced by creating materials from candidates.")
    def __init__(self, value: str):
        self.value = value
