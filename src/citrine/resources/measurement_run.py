"""Resources that represent measurement run data objects."""
from typing import List, Dict, Optional, Type, Iterator, Union
from uuid import UUID

from citrine._rest.resource import GEMDResource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Object, LinkOrElse
from citrine.resources.object_runs import ObjectRun, ObjectRunCollection
from gemd.entity.attribute.condition import Condition
from gemd.entity.attribute.parameter import Parameter
from gemd.entity.attribute.property import Property
from gemd.entity.file_link import FileLink
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object.material_run import MaterialRun as GEMDMaterialRun
from gemd.entity.object.measurement_run import MeasurementRun as GEMDMeasurementRun
from gemd.entity.object.measurement_spec import MeasurementSpec as GEMDMeasurementSpec
from gemd.entity.source.performed_source import PerformedSource


class MeasurementRun(
    GEMDResource['MeasurementRun'],
    ObjectRun,
    GEMDMeasurementRun,
    typ=GEMDMeasurementRun.typ
):
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

    name = String('name', override=True, use_init=True)
    conditions = PropertyOptional(PropertyList(Object(Condition)), 'conditions', override=True)
    parameters = PropertyOptional(PropertyList(Object(Parameter)), 'parameters', override=True)
    properties = PropertyOptional(PropertyList(Object(Property)), 'properties', override=True)
    spec = PropertyOptional(LinkOrElse(GEMDMeasurementSpec), 'spec', override=True, use_init=True,)
    material = PropertyOptional(LinkOrElse(GEMDMaterialRun),
                                "material",
                                override=True,
                                use_init=True,
                                )
    source = PropertyOptional(Object(PerformedSource), "source", override=True)

    def __init__(self,
                 name: str,
                 *,
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
        super(ObjectRun, self).__init__()
        GEMDMeasurementRun.__init__(self, name=name, uids=uids,
                                    material=material,
                                    tags=tags, conditions=conditions, properties=properties,
                                    parameters=parameters, spec=spec,
                                    file_links=file_links, notes=notes, source=source)

    def __str__(self):
        return '<Measurement run {!r}>'.format(self.name)


class MeasurementRunCollection(ObjectRunCollection[MeasurementRun]):
    """Represents the collection of all measurement runs associated with a dataset."""

    _path_template = 'teams/{team_id}/datasets/{dataset_id}/measurement-runs'
    # During this "Projects in Teams" deprication `_path_template` is defined as a Class Variable whereas `_dataset_agnostic_path_template` is defined as a Class Property.
    # This allows for either path to be accessed depending on the user's instantiation of the class.
    # Post-deprication, both can be Class Variables again, using the `teams/...` path.
    _individual_key = 'measurement_run'
    _collection_key = 'measurement_runs'
    _resource = MeasurementRun

    @property
    def _dataset_agnostic_path_template(self):
        if self.project_id is None:
            return 'teams/{self.team_id}/measurement-runs'
        else:
            return 'projects/{self.project_id}/measurement-runs'

    @classmethod
    def get_type(cls) -> Type[MeasurementRun]:
        """Return the resource type in the collection."""
        return MeasurementRun

    def list_by_spec(self,
                     uid: Union[UUID, str, LinkByUID, GEMDMeasurementSpec]
                     ) -> Iterator[MeasurementRun]:
        """
        Get the measurement runs using the specified measurement spec.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDMeasurementSpec]
            A representation of the measurement spec whose measurement run usages are to be located

        Returns
        -------
        Iterator[MeasurementRun]
            The measurement runs using the specified measurement spec.

        """
        return self._get_relation('measurement-specs', uid=uid)

    def list_by_material(self,
                         uid: Union[UUID, str, LinkByUID, GEMDMaterialRun]
                         ) -> Iterator[MeasurementRun]:
        """
        Get measurements of the specified material.

        Parameters
        ----------
        uid: Union[UUID, str, LinkByUID, GEMDMaterialRun]
            A representation of the material whose measurements are to be queried.

        Returns
        -------
        Iterator[MeasurementRun]
            The measurements of the specified material

        """
        return self._get_relation(relation='material-runs', uid=uid)
