"""Resources that represent process spec objects."""
from typing import Optional, Dict, List, Type

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine._serialization.properties import String, Mapping, Object, LinkOrElse
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.ingredient_spec import IngredientSpec
from taurus.entity.file_link import FileLink
from citrine.attributes.condition import Condition
from citrine.attributes.parameter import Parameter
from taurus.entity.object.process_spec import ProcessSpec as TaurusProcessSpec
from taurus.entity.template.process_template import ProcessTemplate as TaurusProcessTemplate


class ProcessSpec(DataConcepts, Resource['ProcessSpec'], TaurusProcessSpec):
    """A process spec."""

    _response_key = TaurusProcessSpec.typ  # 'process_spec"

    name = String('name')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    conditions = PropertyOptional(PropertyList(Object(Condition)), 'conditions')
    parameters = PropertyOptional(PropertyList(Object(Parameter)), 'parameters')
    ingredients = PropertyOptional(
        PropertyList(LinkOrElse()), 'ingredients')
    template = PropertyOptional(LinkOrElse(), 'template')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 conditions: Optional[List[Condition]] = None,
                 parameters: Optional[List[Parameter]] = None,
                 ingredients: Optional[List[IngredientSpec]] = None,
                 template: Optional[TaurusProcessTemplate] = None,
                 file_links: Optional[List[FileLink]] = None):
        DataConcepts.__init__(self, TaurusProcessSpec.typ)
        TaurusProcessSpec.__init__(self, name=name, uids=set_default_uid(uids),
                                   tags=tags, conditions=conditions, parameters=parameters,
                                   ingredients=ingredients, template=template,
                                   file_links=file_links, notes=notes)

    def __str__(self):
        return '<Process spec {!r}>'.format(self.name)


class ProcessSpecCollection(DataConceptsCollection[ProcessSpec]):
    """Represents the collection of all process specs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/process-specs'
    _dataset_agnostic_path_template = 'projects/{project_id}/process-specs'
    _individual_key = 'process_spec'
    _collection_key = 'process_specs'

    @classmethod
    def get_type(cls) -> Type[ProcessSpec]:
        """Return the resource type in the collection."""
        return ProcessSpec
