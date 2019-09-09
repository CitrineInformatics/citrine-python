"""Resources that represent parameter templates."""
from typing import List, Dict, Optional, Type

from citrine._rest.resource import Resource
from citrine._serialization.properties import String, Mapping, Object
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._utils.functions import set_default_uid
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from taurus.entity.template.parameter_template import ParameterTemplate as TaurusParameterTemplate
from taurus.entity.bounds.base_bounds import BaseBounds


class ParameterTemplate(DataConcepts, Resource['ParameterTemplate'], TaurusParameterTemplate):
    """A parameter template."""

    _response_key = TaurusParameterTemplate.typ  # 'parameter_template'

    name = String('name')
    description = PropertyOptional(String(), 'description')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    bounds = Object(BaseBounds, 'bounds')
    typ = String('type')

    def __init__(self,
                 name: str,
                 bounds: BaseBounds,
                 uids: Optional[Dict[str, str]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        DataConcepts.__init__(self, TaurusParameterTemplate.typ)
        TaurusParameterTemplate.__init__(self, name=name, bounds=bounds, tags=tags,
                                         uids=set_default_uid(uids), description=description)

    def __str__(self):
        return '<Parameter template {!r}>'.format(self.name)


class ParameterTemplateCollection(DataConceptsCollection[ParameterTemplate]):
    """A collection of parameter templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/parameter-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/parameter-templates'
    _individual_key = 'parameter_template'
    _collection_key = 'parameter_templates'

    @classmethod
    def get_type(cls) -> Type[ParameterTemplate]:
        """Return the resource type in the collection."""
        return ParameterTemplate
