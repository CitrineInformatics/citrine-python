from warnings import warn

from citrine.resources.table_config import TableConfig
from citrine.resources.table_config import TableConfigCollection


# This is provided for backwards compatibility with the old Ara related names

def AraDefinition(*args, **kwargs):
    """[DEPRECATED] Use TableConfig instead."""
    warn("AraDefinition is deprecated and will soon be removed. "
         "Please use TableConfig instead", DeprecationWarning)
    return TableConfig(*args, **kwargs)


def AraDefinitionCollection(*args, **kwargs):
    """[DEPRECATED] Use TableConfigCollection instead."""
    warn("AraDefinitionCollection is deprecated and will soon be removed. "
         "Please use TableConfigCollection instead", DeprecationWarning)
    return TableConfigCollection(*args, **kwargs)
