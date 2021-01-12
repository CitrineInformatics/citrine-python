"""Top-level class for all template objects and collections thereof."""
from abc import ABC
from typing import TypeVar
from warnings import warn

from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection


class Template(DataConcepts, ABC):
    """
    An abstract template object.

    Template must be extended along with `Resource`
    """


TemplateResourceType = TypeVar("TemplateResourceType", bound="Template")


class TemplateCollection(DataConceptsCollection[TemplateResourceType], ABC):
    """A collection of one kind of template object."""

    def update(self, model: TemplateResourceType) -> TemplateResourceType:
        """Update a template object."""
        warn("Some updates to templates require a longer-running check. Please see async_update "
             "and use that method if it is applicable.", UserWarning)
        return super().update(model)
