"""Stand-ins for the names of features the Citrine Platform has removed.

The platform removed generative design and design space sampling.
Their public names still import, so an existing script reaches a clear error, not an ImportError.
Importing one of these names emits a DeprecationWarning.
Constructing one of the classes, or calling a method on it, raises FeatureRemovedError.
Version 6.0.0 deletes this module and every name it supplies.
"""

from collections.abc import Callable, Iterable
from warnings import warn

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine.exceptions import FeatureRemovedError

DEPRECATED_IN = "5.4.0"
REMOVED_IN = "6.0.0"

GENERATIVE_DESIGN_REMOVED = "Generative design has been removed from the Citrine Platform."
SAMPLING_REMOVED = "Design space sampling has been removed from the Citrine Platform."


class _RemovedClassMeta(type):
    """Raise FeatureRemovedError when code reads a method the removed class no longer has."""

    def __getattr__(cls, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        raise FeatureRemovedError(cls._removal_message)


class _RemovedClass(metaclass=_RemovedClassMeta):
    """Base of a class whose platform feature was removed."""

    _removal_message: str

    def __init__(self, *args, **kwargs):
        raise FeatureRemovedError(self._removal_message)


class GenerativeDesignInput(_RemovedClass):
    """Removed. Constructing one raises :class:`~citrine.exceptions.FeatureRemovedError`."""

    _removal_message = GENERATIVE_DESIGN_REMOVED


class GenerativeDesignResult(_RemovedClass):
    """Removed. Constructing one raises :class:`~citrine.exceptions.FeatureRemovedError`."""

    _removal_message = GENERATIVE_DESIGN_REMOVED


class GenerativeDesignExecution(_RemovedClass):
    """Removed. Constructing one raises :class:`~citrine.exceptions.FeatureRemovedError`."""

    _removal_message = GENERATIVE_DESIGN_REMOVED


class GenerativeDesignExecutionCollection(_RemovedClass):
    """Removed. Constructing one raises :class:`~citrine.exceptions.FeatureRemovedError`."""

    _removal_message = GENERATIVE_DESIGN_REMOVED


class FingerprintType(BaseEnumeration):
    """Removed along with generative design. Its members remain for existing scripts."""

    AP = "AP"
    PHCO = "PHCO"
    BPF = "BPF"
    PATH = "PATH"
    ECFP4 = "ECFP4"
    ECFP6 = "ECFP6"
    FCFP4 = "FCFP4"
    FCFP6 = "FCFP6"


class StructureExclusion(BaseEnumeration):
    """Removed along with generative design. Its members remain for existing scripts."""

    DOUBLE_BONDS = "DOUBLE_BONDS"
    TRIPLE_BONDS = "TRIPLE_BONDS"
    ANIONS = "ANIONS"
    CATIONS = "CATIONS"
    IONS = "IONS"
    BORON = "BORON"
    PHOSPHORUS = "PHOSPHORUS"
    SULFUR = "SULFUR"
    NITROGEN = "NITROGEN"
    OXYGEN = "OXYGEN"
    FLUORINE = "FLUORINE"
    BROMINE = "BROMINE"
    IODINE = "IODINE"
    CHLORINE = "CHLORINE"


class SampleDesignSpaceInput(_RemovedClass):
    """Removed. Constructing one raises :class:`~citrine.exceptions.FeatureRemovedError`."""

    _removal_message = SAMPLING_REMOVED


class SampleDesignSpaceExecution(_RemovedClass):
    """Removed. Constructing one raises :class:`~citrine.exceptions.FeatureRemovedError`."""

    _removal_message = SAMPLING_REMOVED


class SampleDesignSpaceExecutionCollection(_RemovedClass):
    """Removed. Constructing one raises :class:`~citrine.exceptions.FeatureRemovedError`."""

    _removal_message = SAMPLING_REMOVED


class SampleSearchSpaceResultCandidate(_RemovedClass):
    """Removed. Constructing one raises :class:`~citrine.exceptions.FeatureRemovedError`."""

    _removal_message = SAMPLING_REMOVED


_REMOVED_NAMES = {
    cls.__name__: cls
    for cls in (
        GenerativeDesignInput,
        GenerativeDesignResult,
        GenerativeDesignExecution,
        GenerativeDesignExecutionCollection,
        FingerprintType,
        StructureExclusion,
        SampleDesignSpaceInput,
        SampleDesignSpaceExecution,
        SampleDesignSpaceExecutionCollection,
        SampleSearchSpaceResultCandidate,
    )
}


def deprecated_names(
    module_name: str, removal_message: str, names: Iterable[str]
) -> Callable[[str], type]:
    """Build a module ``__getattr__`` that supplies removed names with a DeprecationWarning.

    The legacy module must not bind these names itself.
    Python calls a module's ``__getattr__`` only for names the module lacks.

    Parameters
    ----------
    module_name: str
        The ``__name__`` of the module that used to define the names.
    removal_message: str
        The sentence that states which feature the platform removed.
    names: Iterable[str]
        The removed names the module supplies.

    Returns
    -------
    Callable[[str], type]
        A function to assign to the module's ``__getattr__``.

    """
    supplied = {name: _REMOVED_NAMES[name] for name in names}

    def __getattr__(name: str) -> type:
        if name not in supplied:
            raise AttributeError(f"module {module_name!r} has no attribute {name!r}")
        warn(
            f"{module_name}.{name} is deprecated as of {DEPRECATED_IN} and will be removed "
            f"in {REMOVED_IN}. {removal_message}",
            DeprecationWarning,
            stacklevel=2,
        )
        return supplied[name]

    return __getattr__
