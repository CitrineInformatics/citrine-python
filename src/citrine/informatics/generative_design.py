"""Generative design has been removed; these names remain so existing scripts fail clearly."""

from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine.exceptions import FeatureRemovedError

GENERATIVE_DESIGN_REMOVED = "Generative design has been removed from the Citrine Platform."


class GenerativeDesignInput:
    """Removed. Constructing one raises :class:`~citrine.exceptions.FeatureRemovedError`."""

    def __init__(self, *args, **kwargs):
        raise FeatureRemovedError(GENERATIVE_DESIGN_REMOVED)


class FingerprintType(BaseEnumeration):
    """Removed along with generative design; kept so scripts reach the removal error."""

    AP = "AP"
    PHCO = "PHCO"
    BPF = "BPF"
    PATH = "PATH"
    ECFP4 = "ECFP4"
    ECFP6 = "ECFP6"
    FCFP4 = "FCFP4"
    FCFP6 = "FCFP6"


class StructureExclusion(BaseEnumeration):
    """Removed along with generative design; kept so scripts reach the removal error."""

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
