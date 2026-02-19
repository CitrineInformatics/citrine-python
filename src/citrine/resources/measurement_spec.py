"""Resources that represent measurement spec data objects."""
from collections.abc import Iterator
from uuid import UUID

from citrine._rest.resource import GEMDResource
from citrine._serialization.properties import LinkOrElse, List, Object, Optional, String
from citrine.resources.object_specs import ObjectSpec, ObjectSpecCollection
from gemd.entity.attribute.condition import Condition
from gemd.entity.attribute.parameter import Parameter
from gemd.entity.file_link import FileLink
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.measurement_spec import MeasurementSpec as GEMDMeasurementSpec
from gemd.entity.template.measurement_template import \
    MeasurementTemplate as GEMDMeasurementTemplate


class MeasurementSpec(
    GEMDResource['MeasurementSpec'],
    ObjectSpec,
    GEMDMeasurementSpec,
    typ=GEMDMeasurementSpec.typ
):
    """
    A measurement specification.

    Parameters
    ----------
    name: str
        Name of the measurement spec.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: list[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the measurement spec.
    conditions: list[Condition], optional
        Conditions under which this measurement spec occurs.
    parameters: list[Parameter], optional
        Parameters of this measurement spec.
    template: MeasurementTemplate
        A template bounding the valid values for the measurement's properties, parameters,
        and conditions.
    file_links: list[FileLink], optional
        Links to associated files, with resource paths into the files API.

    """

    _response_key = GEMDMeasurementSpec.typ  # 'measurement_spec'

    name = String('name', override=True, use_init=True)
    conditions = Optional(List(Object(Condition)), 'conditions', override=True)
    parameters = Optional(List(Object(Parameter)), 'parameters', override=True)
    template = Optional(LinkOrElse(GEMDMeasurementTemplate), 'template', override=True,
                        use_init=True)

    def __init__(self,
                 name: str,
                 *,
                 uids: dict[str, str] | None = None,
                 tags: list[str] | None = None,
                 notes: str | None = None,
                 conditions: list[Condition] | None = None,
                 parameters: list[Parameter] | None = None,
                 template: GEMDMeasurementTemplate | None = None,
                 file_links: list[FileLink] | None = None):
        if uids is None:
            uids = dict()
        super(ObjectSpec, self).__init__()
        GEMDMeasurementSpec.__init__(self, name=name, uids=uids,
                                     tags=tags, conditions=conditions, parameters=parameters,
                                     template=template, file_links=file_links, notes=notes)

    def __str__(self):
        return '<Measurement spec {!r}>'.format(self.name)


class MeasurementSpecCollection(ObjectSpecCollection[MeasurementSpec]):
    """Represents the collection of all measurement specs associated with a dataset."""

    _individual_key = 'measurement_spec'
    _collection_key = 'measurement_specs'
    _resource = MeasurementSpec

    @classmethod
    def get_type(cls) -> type[MeasurementSpec]:
        """Return the resource type in the collection."""
        return MeasurementSpec

    def list_by_template(self,
                         uid: UUID | str | LinkByUID | GEMDMeasurementTemplate
                         ) -> Iterator[MeasurementSpec]:
        """
        Get the measurement specs using the specified measurement template.

        Parameters
        ----------
        uid: UUID | str | LinkByUID | GEMDMeasurementTemplate
            A representation of of the measurement template whose measurement spec usages are
            to be located.

        Returns
        -------
        Iterator[MeasurementSpec]
            The measurement specs using the specified measurement template.

        """
        return self._get_relation('measurement-templates', uid=uid)
