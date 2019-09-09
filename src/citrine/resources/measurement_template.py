"""Resources that represent measurement templates."""
from typing import List, Dict, Optional, Union, Sequence, Type

from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._serialization.properties import String, Mapping, Object, MixedList, LinkOrElse
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._utils.functions import set_default_uid
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.property_template import PropertyTemplate
from citrine.resources.parameter_template import ParameterTemplate
from citrine.resources.condition_template import ConditionTemplate
from taurus.client.json_encoder import loads, dumps
from taurus.entity.template.measurement_template \
    import MeasurementTemplate as TaurusMeasurementTemplate
from taurus.entity.bounds.base_bounds import BaseBounds
from taurus.entity.link_by_uid import LinkByUID


class MeasurementTemplate(DataConcepts, Resource['MeasurementTemplate'],
                          TaurusMeasurementTemplate):
    """A measurement template."""

    _response_key = TaurusMeasurementTemplate.typ  # 'measurement_template'

    name = String('name')
    description = PropertyOptional(String(), 'description')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    properties = PropertyOptional(PropertyList(
        MixedList([LinkOrElse, Object(BaseBounds)])), 'properties')
    conditions = PropertyOptional(PropertyList(
        MixedList([LinkOrElse, Object(BaseBounds)])), 'conditions')
    parameters = PropertyOptional(PropertyList(
        MixedList([LinkOrElse, Object(BaseBounds)])), 'parameters')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 properties: Optional[Sequence[Union[PropertyTemplate,
                                                     LinkByUID,
                                                     Sequence[Union[PropertyTemplate, LinkByUID,
                                                                    BaseBounds]]
                                                     ]]] = None,
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
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        DataConcepts.__init__(self, TaurusMeasurementTemplate.typ)
        TaurusMeasurementTemplate.__init__(self, name=name, properties=properties,
                                           conditions=conditions, parameters=parameters, tags=tags,
                                           uids=set_default_uid(uids), description=description)

    @classmethod
    def _build_child_objects(cls, data: dict, session: Session = None):
        if 'properties' in data and len(data['properties']) != 0:
            data['properties'] = [[PropertyTemplate.build(prop[0].as_dict()),
                                   loads(dumps(prop[1]))] for prop in data['properties']]
        if 'conditions' in data and len(data['conditions']) != 0:
            data['conditions'] = [[ConditionTemplate.build(prop[0].as_dict()),
                                   loads(dumps(prop[1]))] for prop in data['conditions']]
        if 'parameters' in data and len(data['parameters']) != 0:
            data['parameters'] = [[ParameterTemplate.build(prop[0].as_dict()),
                                   loads(dumps(prop[1]))] for prop in data['parameters']]

    def __str__(self):
        return '<Measurement template {!r}>'.format(self.name)


class MeasurementTemplateCollection(DataConceptsCollection[MeasurementTemplate]):
    """A collection of measurement templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/measurement-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/measurement-templates'
    _individual_key = 'measurement_template'
    _collection_key = 'measurement_templates'

    @classmethod
    def get_type(cls) -> Type[MeasurementTemplate]:
        """Return the resource type in the collection."""
        return MeasurementTemplate
