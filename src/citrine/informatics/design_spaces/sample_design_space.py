"""Design space sampling has been removed; this name remains so existing scripts fail clearly."""

from citrine.exceptions import FeatureRemovedError

SAMPLING_REMOVED = "Design space sampling has been removed from the Citrine Platform."


class SampleDesignSpaceInput:
    """Removed. Constructing one raises :class:`~citrine.exceptions.FeatureRemovedError`."""

    def __init__(self, *args, **kwargs):
        raise FeatureRemovedError(SAMPLING_REMOVED)
