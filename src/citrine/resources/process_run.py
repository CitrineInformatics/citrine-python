"""Resources that represent process run data objects."""
from typing import List, Dict, Optional, Type

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine._serialization.properties import String, Mapping, Object, LinkOrElse
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine.resources.ingredient_run import IngredientRun
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from taurus.entity.file_link import FileLink
from citrine.attributes.condition import Condition
from citrine.attributes.parameter import Parameter
from taurus.entity.object.process_run import ProcessRun as TaurusProcessRun
from taurus.entity.object.process_spec import ProcessSpec as TaurusProcessSpec


class ProcessRun(DataConcepts, Resource['ProcessRun'], TaurusProcessRun):
    """A process run."""

    _response_key = TaurusProcessRun.typ  # 'process_run'

    name = String('name')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    conditions = PropertyOptional(PropertyList(Object(Condition)), 'conditions')
    parameters = PropertyOptional(PropertyList(Object(Parameter)), 'parameters')
    ingredients = PropertyOptional(
        PropertyList(LinkOrElse()), 'ingredients')
    spec = PropertyOptional(LinkOrElse(), 'spec')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 conditions: Optional[List[Condition]] = None,
                 parameters: Optional[List[Parameter]] = None,
                 ingredients: Optional[List[IngredientRun]] = None,
                 spec: Optional[TaurusProcessSpec] = None,
                 file_links: Optional[List[FileLink]] = None):
        DataConcepts.__init__(self, TaurusProcessRun.typ)
        TaurusProcessRun.__init__(self, name=name, uids=set_default_uid(uids),
                                  tags=tags, conditions=conditions, parameters=parameters,
                                  ingredients=ingredients, spec=spec,
                                  file_links=file_links, notes=notes)

    def __str__(self):
        return '<Process run {!r}>'.format(self.name)


class ProcessRunCollection(DataConceptsCollection[ProcessRun]):
    """Represents the collection of all process runs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/process-runs'
    _dataset_agnostic_path_template = 'projects/{project_id}/process-runs'
    _individual_key = 'process_run'
    _collection_key = 'process_runs'

    @classmethod
    def get_type(cls) -> Type[ProcessRun]:
        """Return the resource type in the collection."""
        return ProcessRun
