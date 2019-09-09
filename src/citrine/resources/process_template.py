"""Resources that represent process templates."""
from typing import List, Dict, Optional, Union, Sequence, Type

from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._serialization.properties import String, Mapping, Object, MixedList, LinkOrElse
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._utils.functions import set_default_uid
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.parameter_template import ParameterTemplate
from citrine.resources.condition_template import ConditionTemplate
from taurus.client.json_encoder import loads, dumps
from taurus.entity.template.process_template import ProcessTemplate as TaurusProcessTemplate
from taurus.entity.bounds.base_bounds import BaseBounds
from taurus.entity.link_by_uid import LinkByUID


class ProcessTemplate(DataConcepts, Resource['ProcessTemplate'], TaurusProcessTemplate):
    """A process template."""

    _response_key = TaurusProcessTemplate.typ  # 'process_template'

    name = String('name')
    description = PropertyOptional(String(), 'description')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    conditions = PropertyOptional(PropertyList(
        MixedList([LinkOrElse, Object(BaseBounds)])), 'conditions')
    parameters = PropertyOptional(PropertyList(
        MixedList([LinkOrElse, Object(BaseBounds)])), 'parameters')
    allowed_labels = PropertyOptional(PropertyList(String()), 'allowed_labels')
    allowed_unique_labels = PropertyOptional(PropertyList(String()), 'allowed_unique_labels')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 conditions: Optional[Sequence[Union[ConditionTemplate,
                                                     LinkByUID,
                                                     Sequence[Union[ConditionTemplate, LinkByUID,
                                                                    BaseBounds]]
                                                     ]]] = None,
                 parameters: Optional[Sequence[Union[ParameterTemplate,
                                                     LinkByUID,
                                                     Sequence[Union[ParameterTemplate, LinkByUID,
                                                                    BaseBounds]]
                                                     ]]] = None,
                 allowed_labels: Optional[List[str]] = None,
                 allowed_unique_labels: Optional[List[str]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        DataConcepts.__init__(self, TaurusProcessTemplate.typ)
        TaurusProcessTemplate.__init__(self, name=name, uids=set_default_uid(uids),
                                       conditions=conditions, parameters=parameters, tags=tags,
                                       description=description, allowed_labels=allowed_labels,
                                       allowed_unique_labels=allowed_unique_labels)

    @classmethod
    def _build_child_objects(cls, data: dict, session: Session = None):
        if 'conditions' in data and len(data['conditions']) != 0:
            data['conditions'] = [[ConditionTemplate.build(prop[0].as_dict()),
                                   loads(dumps(prop[1]))] for prop in data['conditions']]
        if 'parameters' in data and len(data['parameters']) != 0:
            data['parameters'] = [[ParameterTemplate.build(prop[0].as_dict()),
                                   loads(dumps(prop[1]))] for prop in data['parameters']]

    def __str__(self):
        return '<Process template {!r}>'.format(self.name)


class ProcessTemplateCollection(DataConceptsCollection[ProcessTemplate]):
    """A collection of process templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/process-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/process-templates'
    _individual_key = 'process_template'
    _collection_key = 'process_templates'

    @classmethod
    def get_type(cls) -> Type[ProcessTemplate]:
        """Return the resource type in the collection."""
        return ProcessTemplate
