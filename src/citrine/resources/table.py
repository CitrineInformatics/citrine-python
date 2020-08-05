from warnings import warn  # pragma: no cover

from citrine.resources.gemtables import GemTableCollection, GemTable  # pragma: no cover


def Table(*args, **kwargs):  # pragma: no cover
    """[DEPRECATED] Use GemTable instead."""
    warn("Table is deprecated and will soon be removed. "
         "Please use GemTable instead", DeprecationWarning)
    return GemTable(*args, **kwargs)


def TableCollection(*args, **kwargs):  # pragma: no cover
    """[DEPRECATED] Use GemTableCollection instead."""
    warn("TableCollection is deprecated and will soon be removed. "
         "Please use GemTableCollection instead", DeprecationWarning)
    return GemTableCollection(*args, **kwargs)
