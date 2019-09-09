"""Resources that represent material run data objects."""
from typing import List, Dict, Optional, Type
import os
import json

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine._serialization.properties import String, LinkOrElse, Mapping, Object
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from taurus.client.json_encoder import TaurusEncoder
from taurus.entity.file_link import FileLink
from taurus.entity.object.process_run import ProcessRun as TaurusProcessRun
from taurus.entity.object.measurement_run import MeasurementRun as TaurusMeasurementRun
from taurus.entity.object.material_run import MaterialRun as TaurusMaterialRun
from taurus.entity.object.material_spec import MaterialSpec as TaurusMaterialSpec
from taurus.client.json_encoder import loads


class MaterialRun(DataConcepts, Resource['MaterialRun'], TaurusMaterialRun):
    """A material run."""

    _response_key = TaurusMaterialRun.typ  # 'material_run'

    name = String('name')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    process = PropertyOptional(LinkOrElse(), 'process')
    sample_type = String('sample_type')
    spec = PropertyOptional(LinkOrElse(), 'spec')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 process: Optional[TaurusProcessRun] = None,
                 sample_type: Optional[str] = "unknown",
                 spec: Optional[TaurusMaterialSpec] = None,
                 file_links: Optional[List[FileLink]] = None,
                 measurements: Optional[List[TaurusMeasurementRun]] = None):
        DataConcepts.__init__(self, TaurusMaterialRun.typ)
        TaurusMaterialRun.__init__(self, name=name, uids=set_default_uid(uids),
                                   tags=tags, process=process,
                                   sample_type=sample_type, spec=spec,
                                   file_links=file_links, notes=notes)

    def __str__(self):
        return '<Material run {!r}>'.format(self.name)


class MaterialRunCollection(DataConceptsCollection[MaterialRun]):
    """Represents the collection of all material runs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/material-runs'
    _dataset_agnostic_path_template = 'projects/{project_id}/material-runs'
    _individual_key = 'material_run'
    _collection_key = 'material_runs'

    @classmethod
    def get_type(cls) -> Type[MaterialRun]:
        """Return the resource type in the collection."""
        return MaterialRun

    def get_history(self, scope, id):
        """Get the history associated with a material."""
        base_path = os.path.dirname(self._get_path(ignore_dataset=True))
        path = base_path + "/material-history/{}/{}".format(scope, id)
        data = self.session.get_resource(path)
        # Rehydrate a taurus object based on the data
        model = loads(json.dumps([data['context'], data['root']], cls=TaurusEncoder))
        # Convert taurus objects into citrine-python objects
        return MaterialRun.build(model.as_dict())
