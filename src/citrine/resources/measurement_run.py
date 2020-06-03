"""Resources that represent measurement run data objects."""
from typing import List, Dict, Optional, Type, Iterator, Union
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Object, Mapping, LinkOrElse
from citrine.resources.data_concepts import DataConcepts
from citrine.resources.object_runs import ObjectRun, ObjectRunCollection
from gemd.entity.attribute.condition import Condition
from gemd.entity.attribute.parameter import Parameter
from gemd.entity.attribute.property import Property
from gemd.entity.file_link import FileLink
from gemd.entity.object.material_run import MaterialRun as GEMDMaterialRun
from gemd.entity.object.measurement_run import MeasurementRun as GEMDMeasurementRun
from gemd.entity.object.measurement_spec import MeasurementSpec as GEMDMeasurementSpec
from gemd.entity.source.performed_source import PerformedSource


class MeasurementRun(ObjectRun, Resource['MeasurementRun'], GEMDMeasurementRun):
    """
    A measurement run.

    Parameters
    ----------
    name: str
        Name of the measurement run.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the measurement run.
    conditions: List[Condition], optional
        Conditions under which this measurement run occurs.
    parameters: List[Parameter], optional
        Parameters of this measurement run.
    properties: List[Property], optional
        Properties that are measured during this measurement run.
    spec: MeasurementSpec
        The measurement specification of which this is an instance.
    material: MaterialRun
        The material run being measured.
    spec: MaterialSpec
        The material specification of which this is an instance.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.
    source: PerformedSource, optional
        Information about the person who performed the run and when.

    """

    _response_key = GEMDMeasurementRun.typ  # 'measurement_run'

    name = String('name')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    conditions = PropertyOptional(PropertyList(Object(Condition)), 'conditions')
    parameters = PropertyOptional(PropertyList(Object(Parameter)), 'parameters')
    properties = PropertyOptional(PropertyList(Object(Property)), 'properties')
    spec = PropertyOptional(LinkOrElse(), 'spec')
    material = PropertyOptional(LinkOrElse(), "material")
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    source = PropertyOptional(Object(PerformedSource), "source")
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 conditions: Optional[List[Condition]] = None,
                 properties: Optional[List[Property]] = None,
                 parameters: Optional[List[Parameter]] = None,
                 spec: Optional[GEMDMeasurementSpec] = None,
                 material: Optional[GEMDMaterialRun] = None,
                 file_links: Optional[List[FileLink]] = None,
                 source: Optional[PerformedSource] = None):
        if uids is None:
            uids = dict()
        DataConcepts.__init__(self, GEMDMeasurementRun.typ)
        GEMDMeasurementRun.__init__(self, name=name, uids=uids,
                                    material=material,
                                    tags=tags, conditions=conditions, properties=properties,
                                    parameters=parameters, spec=spec,
                                    file_links=file_links, notes=notes, source=source)

    def __str__(self):
        return '<Measurement run {!r}>'.format(self.name)


class MeasurementRunCollection(ObjectRunCollection[MeasurementRun]):
    """Represents the collection of all measurement runs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/measurement-runs'
    _dataset_agnostic_path_template = 'projects/{project_id}/measurement-runs'
    _individual_key = 'measurement_run'
    _collection_key = 'measurement_runs'

    @classmethod
    def get_type(cls) -> Type[MeasurementRun]:
        """Return the resource type in the collection."""
        return MeasurementRun

    def list_by_spec(self, uid: Union[UUID, str], scope: str = 'id') -> Iterator[MeasurementRun]:
        """
        [ALPHA] Get the measurement runs using the specified measurement spec.

        Parameters
        ----------
        uid
            The unique ID of the measurement spec whose measurement run usages are to be located.
        scope
            The scope of `uid`.
        Returns
        -------
        Iterator[MeasurementRun]
            The measurement runs using the specified measurement spec.

        """
        return self._get_relation('measurement-specs', uid=uid, scope=scope)

    def list_by_material(self, uid: Union[UUID, str],
                         scope: str = 'id') -> Iterator[MeasurementRun]:
        """
        [ALPHA] Get measurements of the specified material.

        Parameters
        ----------
        uid
            The unique ID of the material whose measurements are to be queried.
        scope
            The scope of `uid`.
        Returns
        -------
        Iterator[MeasurementRun]
            The measurements of the specified material

        """
        return self._get_relation(relation='material-runs', uid=uid, scope=scope)
