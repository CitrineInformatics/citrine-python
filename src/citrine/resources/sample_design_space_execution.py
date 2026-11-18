"""Design space sampling has been removed from the Citrine Platform.

Importing a name from this module emits a DeprecationWarning.
Using one of its classes raises :class:`~citrine.exceptions.FeatureRemovedError`.
"""

from citrine._utils import removed_features

__getattr__ = removed_features.deprecated_names(
    __name__,
    removed_features.SAMPLING_REMOVED,
    [
        "SampleDesignSpaceExecutionCollection",
        "SampleDesignSpaceExecution",
        "SampleDesignSpaceInput",
    ],
)
