"""Resources that represent material templates."""
from typing import List, Dict, Optional, Union, Sequence, Type

from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._serialization.properties import String, Mapping, Object, MixedList, LinkOrElse
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._utils.functions import set_default_uid
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.property_template import PropertyTemplate
from taurus.client.json_encoder import loads, dumps
from taurus.entity.template.material_template import MaterialTemplate as TaurusMaterialTemplate
from taurus.entity.bounds.base_bounds import BaseBounds
from taurus.entity.link_by_uid import LinkByUID


class MaterialTemplate(DataConcepts, Resource['MaterialTemplate'], TaurusMaterialTemplate):
    """A material template."""

    _response_key = TaurusMaterialTemplate.typ  # 'material_template'

    name = String('name')
    description = PropertyOptional(String(), 'description')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    properties = PropertyOptional(PropertyList(
        MixedList([LinkOrElse, Object(BaseBounds)])), 'properties')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 properties: Optional[Sequence[Union[PropertyTemplate,
                                                     LinkByUID,
                                                     Sequence[Union[PropertyTemplate, LinkByUID,
                                                                    BaseBounds]]
                                                     ]]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        # properties is a list, each element of which is a PropertyTemplate OR is a list with
        # 2 entries: [PropertyTemplate, BaseBounds]. Python typing is not expressive enough, so
        # the typing above is more general.
        DataConcepts.__init__(self, TaurusMaterialTemplate.typ)
        TaurusMaterialTemplate.__init__(self, name=name, properties=properties,
                                        uids=set_default_uid(uids), tags=tags,
                                        description=description)

    @classmethod
    def _build_child_objects(cls, data: dict, session: Session = None):
        if 'properties' in data and len(data['properties']) != 0:
            # Each entry in the list data['properties'] has a property template as the 1st entry
            # and a base bounds as the 2nd entry. They are built in different ways.
            data['properties'] = [[PropertyTemplate.build(prop[0].as_dict()),
                                   loads(dumps(prop[1]))] for prop in data['properties']]

    def __str__(self):
        return '<Material template {!r}>'.format(self.name)


class MaterialTemplateCollection(DataConceptsCollection[MaterialTemplate]):
    """A collection of material templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/material-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/material-templates'
    _individual_key = 'material_template'
    _collection_key = 'material_templates'

    @classmethod
    def get_type(cls) -> Type[MaterialTemplate]:
        """Return the resource type in the collection."""
        return MaterialTemplate
