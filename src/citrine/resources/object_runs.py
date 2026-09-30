"""Top-level class for all object run objects and collections thereof."""

from abc import ABC, abstractmethod
from typing import TypeVar

from gemd.entity.base_entity import BaseEntity
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.has_spec import HasSpec
from gemd.entity.object.has_template import HasTemplate
from gemd.entity.template.base_template import BaseTemplate

from citrine.resources.data_objects import DataObject, DataObjectCollection


class ObjectRun(DataObject, HasSpec, ABC):
    """
    An abstract object run object.

    ObjectRun must be extended along with `Resource`
    """


class TemplatedObjectRun(ObjectRun, ABC):
    """
    An abstract object run that can reference its template directly.

    The run's own template takes precedence over the template of its spec.
    Only a template set on the run itself is sent to the platform; the template of the spec
    is never copied onto the run.

    Subclasses declare the serialized ``_template`` field and the accepted template type.
    """

    @staticmethod
    @abstractmethod
    def _template_type() -> type:
        """Return the template type this run accepts."""

    @property
    def template(self) -> BaseTemplate | LinkByUID | None:
        """The run's own template when set, otherwise the template of its spec."""
        if self._template is not None:
            return self._template
        return super().template

    @template.setter
    def template(self, template: BaseTemplate | LinkByUID | None):
        if template is not None and not isinstance(template, (self._template_type(), LinkByUID)):
            raise TypeError(
                f"template must be a {self._template_type().__name__} or LinkByUID, "
                f"not {type(template)}"
            )
        self._template = template

    def _local_dependencies(self) -> set[BaseEntity | LinkByUID]:
        """Return the spec and the run's own template, when set."""
        return {x for x in (self.spec, self._template) if x is not None}

    def _dict_for_compare(self) -> dict:
        """Support for recursive equals."""
        result = super()._dict_for_compare()
        # A gemd run that mixes in HasTemplate has a template key in its as_dict; one that
        # does not has no such key, so the key is dropped to keep the two comparable.
        if not isinstance(self, HasTemplate):
            result.pop("template", None)
        return result


ObjectRunResourceType = TypeVar("ObjectRunResourceType", bound="ObjectRun")


class ObjectRunCollection(DataObjectCollection[ObjectRunResourceType], ABC):
    """A collection of one kind of object run object."""
