"""Resources that represent property templates."""
from typing import List, Dict, Optional, Type

from citrine._rest.resource import Resource
from citrine._serialization.properties import String, Mapping, Object
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._utils.functions import set_default_uid
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from taurus.entity.template.property_template import PropertyTemplate as TaurusPropertyTemplate
from taurus.entity.bounds.base_bounds import BaseBounds


class PropertyTemplate(DataConcepts, Resource['PropertyTemplate'], TaurusPropertyTemplate):
    """A property template."""

    _response_key = TaurusPropertyTemplate.typ  # 'property_template'

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
        DataConcepts.__init__(self, TaurusPropertyTemplate.typ)
        TaurusPropertyTemplate.__init__(self, name=name, bounds=bounds, tags=tags,
                                        uids=set_default_uid(uids), description=description)

    def __str__(self):
        return '<Property template {!r}>'.format(self.name)


class PropertyTemplateCollection(DataConceptsCollection[PropertyTemplate]):
    """A collection of property templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/property-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/property-templates'
    _individual_key = 'property_template'
    _collection_key = 'property_templates'

    @classmethod
    def get_type(cls) -> Type[PropertyTemplate]:
        """Return the resource type in the collection."""
        return PropertyTemplate
