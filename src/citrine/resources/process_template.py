"""Resources that represent process templates."""

from collections.abc import Sequence

from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.template.condition_template import ConditionTemplate as GEMDConditionTemplate
from gemd.entity.template.parameter_template import ParameterTemplate as GEMDParameterTemplate
from gemd.entity.template.process_template import ProcessTemplate as GEMDProcessTemplate

from citrine._rest.resource import GEMDResource
from citrine._serialization.properties import List, Optional, String
from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.object_templates import (
    ObjectTemplate,
    ObjectTemplateCollection,
    _attr_tuple,
)
from citrine.resources.parameter_template import ParameterTemplate


class ProcessTemplate(
    GEMDResource["ProcessTemplate"],
    ObjectTemplate,
    GEMDProcessTemplate,
    typ=GEMDProcessTemplate.typ,
):
    """
    A process template.

    Process templates are collections of condition and parameter templates that constrain the
    values of a measurement's condition and parameter attributes, and provide a common structure
    for describing similar measurements.

    Parameters
    ----------
    name: str
        The name of the process template.
    description: str, optional
        Long-form description of the process template.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: list[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    conditions: list[ConditionTemplate] or list[ConditionTemplate, \
    :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated conditions. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this condition.
    parameters: list[ParameterTemplate] or list[ParameterTemplate, \
    :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated parameters. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this parameter.

    """

    _response_key = GEMDProcessTemplate.typ  # 'process_template'

    conditions = Optional(List(_attr_tuple(GEMDConditionTemplate)), "conditions", override=True)
    parameters = Optional(List(_attr_tuple(GEMDParameterTemplate)), "parameters", override=True)

    allowed_labels = Optional(List(String()), "allowed_labels", override=True)
    allowed_names = Optional(List(String()), "allowed_names", override=True)

    def __init__(
        self,
        name: str,
        *,
        uids: dict[str, str] | None = None,
        conditions: Sequence[
            ConditionTemplate
            | LinkByUID
            | Sequence[ConditionTemplate | LinkByUID | BaseBounds | None]
        ]
        | None = None,
        parameters: Sequence[
            ParameterTemplate
            | LinkByUID
            | Sequence[ParameterTemplate | LinkByUID | BaseBounds | None]
        ]
        | None = None,
        allowed_labels: list[str] | None = None,
        allowed_names: list[str] | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ):
        if uids is None:
            uids = dict()
        super(ObjectTemplate, self).__init__()
        GEMDProcessTemplate.__init__(
            self,
            name=name,
            uids=uids,
            conditions=conditions,
            parameters=parameters,
            tags=tags,
            description=description,
            allowed_labels=allowed_labels,
            allowed_names=allowed_names,
        )

    def __str__(self):
        return f"<Process template {self.name!r}>"


class ProcessTemplateCollection(ObjectTemplateCollection[ProcessTemplate]):
    """A collection of process templates."""

    _individual_key = "process_template"
    _collection_key = "process_templates"
    _resource = ProcessTemplate

    @classmethod
    def get_type(cls) -> type[ProcessTemplate]:
        """Return the resource type in the collection."""
        return ProcessTemplate
