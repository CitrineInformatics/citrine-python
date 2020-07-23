from warnings import warn

from citrine.resources.gemtables import GemTableCollection, GemTable


def Table(*args, **kwargs):
    """[DEPRECATED] Use GemTable instead."""
    warn("Table is deprecated and will soon be removed. "
         "Please use GemTable instead", DeprecationWarning)
    return GemTable(*args, **kwargs)


def TableCollection(*args, **kwargs):
    """[DEPRECATED] Use GemTableCollection instead."""
    warn("TableCollection is deprecated and will soon be removed. "
         "Please use GemTableCollection instead", DeprecationWarning)
    return GemTableCollection(*args, **kwargs)
