"""Resources that represent process spec objects."""
from collections.abc import Iterator
from uuid import UUID

from citrine._rest.resource import GEMDResource
from citrine._serialization.properties import List, LinkOrElse, Object, Optional, String
from citrine.resources.object_specs import ObjectSpec, ObjectSpecCollection
from gemd.entity.attribute.condition import Condition
from gemd.entity.attribute.parameter import Parameter
from gemd.entity.file_link import FileLink
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.process_spec import ProcessSpec as GEMDProcessSpec
from gemd.entity.template.process_template import ProcessTemplate as GEMDProcessTemplate


class ProcessSpec(
    GEMDResource['ProcessSpec'],
    ObjectSpec,
    GEMDProcessSpec,
    typ=GEMDProcessSpec.typ
):
    """
    A process specification.

    Processes transform zero or more input materials into exactly one output material.

    Parameters
    ----------
    name: str
        Name of the process spec.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: list[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the process spec.
    conditions: list[Condition], optional
        Conditions under which this process spec occurs.
    parameters: list[Parameter], optional
        Parameters of this process spec.
    template: ProcessTemplate, optional
        A template bounding the valid values for this process's parameters and conditions.
    file_links: list[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = GEMDProcessSpec.typ  # 'process_spec'

    name = String('name', override=True, use_init=True)
    conditions = Optional(List(Object(Condition)), 'conditions', override=True)
    parameters = Optional(List(Object(Parameter)), 'parameters', override=True)
    template = Optional(LinkOrElse(GEMDProcessTemplate), 'template', override=True, use_init=True)

    def __init__(self,
                 name: str,
                 *,
                 uids: dict[str, str] | None = None,
                 tags: list[str] | None = None,
                 notes: str | None = None,
                 conditions: list[Condition] | None = None,
                 parameters: list[Parameter] | None = None,
                 template: GEMDProcessTemplate | None = None,
                 file_links: list[FileLink] | None = None
                 ):
        if uids is None:
            uids = dict()
        super(ObjectSpec, self).__init__()
        GEMDProcessSpec.__init__(self, name=name, uids=uids,
                                 tags=tags, conditions=conditions, parameters=parameters,
                                 template=template, file_links=file_links, notes=notes)

    def __str__(self):
        return '<Process spec {!r}>'.format(self.name)


class ProcessSpecCollection(ObjectSpecCollection[ProcessSpec]):
    """Represents the collection of all process specs associated with a dataset."""

    _individual_key = 'process_spec'
    _collection_key = 'process_specs'
    _resource = ProcessSpec

    @classmethod
    def get_type(cls) -> type[ProcessSpec]:
        """Return the resource type in the collection."""
        return ProcessSpec

    def list_by_template(self,
                         uid: UUID | str | LinkByUID | GEMDProcessTemplate
                         ) -> Iterator[ProcessSpec]:
        """
        Get the process specs using the specified process template.

        Parameters
        ----------
        uid: UUID | str | LinkByUID | GEMDProcessTemplate
            A representation of the process template whose process spec usages are to be located.

        Returns
        -------
        Iterator[ProcessSpec]
            The process specs using the specified process template

        """
        return self._get_relation('process-templates', uid=uid)
