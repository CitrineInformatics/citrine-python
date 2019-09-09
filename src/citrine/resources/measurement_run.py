"""Resources that represent measurement run data objects."""
from typing import List, Dict, Optional, Type

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine._serialization.properties import String, Object, Mapping, LinkOrElse
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from taurus.entity.file_link import FileLink
from citrine.attributes.condition import Condition
from citrine.attributes.parameter import Parameter
from citrine.attributes.property import Property
from taurus.entity.object.material_run import MaterialRun as TaurusMaterialRun
from taurus.entity.object.measurement_run import MeasurementRun as TaurusMeasurementRun
from taurus.entity.object.measurement_spec import MeasurementSpec as TaurusMeasurementSpec


class MeasurementRun(DataConcepts, Resource['MeasurementRun'], TaurusMeasurementRun):
    """A measurement run."""

    _response_key = TaurusMeasurementRun.typ  # 'measurement_run'

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
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 conditions: Optional[List[Condition]] = None,
                 properties: Optional[List[Property]] = None,
                 parameters: Optional[List[Parameter]] = None,
                 spec: Optional[TaurusMeasurementSpec] = None,
                 material: Optional[TaurusMaterialRun] = None,
                 file_links: Optional[List[FileLink]] = None):
        DataConcepts.__init__(self, TaurusMeasurementRun.typ)
        TaurusMeasurementRun.__init__(self, name=name, uids=set_default_uid(uids),
                                      material=material,
                                      tags=tags, conditions=conditions, properties=properties,
                                      parameters=parameters, spec=spec,
                                      file_links=file_links, notes=notes)

    def __str__(self):
        return '<Measurement run {!r}>'.format(self.name)


class MeasurementRunCollection(DataConceptsCollection[MeasurementRun]):
    """Represents the collection of all measurement runs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/measurement-runs'
    _dataset_agnostic_path_template = 'projects/{project_id}/measurement-runs'
    _individual_key = 'measurement_run'
    _collection_key = 'measurement_runs'

    @classmethod
    def get_type(cls) -> Type[MeasurementRun]:
        """Return the resource type in the collection."""
        return MeasurementRun
