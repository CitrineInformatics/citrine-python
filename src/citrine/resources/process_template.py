"""Resources that represent process templates."""
from typing import List, Dict, Optional, Union, Sequence, Type

from citrine._rest.resource import Resource
from citrine._session import Session
from citrine._serialization.properties import String, Mapping, Object, MixedList, LinkOrElse
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import List as PropertyList
from citrine._utils.functions import set_default_uid
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine.resources.storable import Storable
from citrine.resources.parameter_template import ParameterTemplate
from citrine.resources.condition_template import ConditionTemplate
from taurus.client.json_encoder import loads, dumps
from taurus.entity.template.process_template import ProcessTemplate as TaurusProcessTemplate
from taurus.entity.bounds.base_bounds import BaseBounds
from taurus.entity.link_by_uid import LinkByUID


class ProcessTemplate(Storable, Resource['ProcessTemplate'], TaurusProcessTemplate):
    """
    A process template.

    Process templates are collections of condition and parameter templates that constrain the
    values of a measurement's condition and parameter attributes, and provide a common structure
    for describing similar measurements.

    Parameters
    ----------
    name: str
        The name of the process template.
    description: str, optional
        Long-form description of the process template.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/taurus-documentation/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/taurus-documentation/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    conditions: List[ConditionTemplate] or List[ConditionTemplate, \
    :py:class:`BaseBounds <taurus.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated conditions. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this condition.
    parameters: List[ParameterTemplate] or List[ParameterTemplate, \
    :py:class:`BaseBounds <taurus.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated parameters. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this parameter.

    """

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
    allowed_names = PropertyOptional(PropertyList(String()), 'allowed_names')
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
                 allowed_names: Optional[List[str]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        DataConcepts.__init__(self, TaurusProcessTemplate.typ)
        TaurusProcessTemplate.__init__(self, name=name, uids=set_default_uid(uids),
                                       conditions=conditions, parameters=parameters, tags=tags,
                                       description=description, allowed_labels=allowed_labels,
                                       allowed_names=allowed_names)

    @classmethod
    def _build_child_objects(cls, data: dict, data_with_soft_links, session: Session = None):
        """
        Build the condition and parameter templates and bounds.

        Parameters
        ----------
        data: dict
            A serialized material template.
        session: Session, optional
            Citrine session used to connect to the database.

        Returns
        -------
        None
            The serialized process template is modified so that its conditions are now a list
            of object pairs of the form [ConditionTemplate,
            :py:class:`BaseBounds <taurus.entity.bounds.base_bounds.BaseBounds>`],
            and the parameters are [ParameterTemplate,
            :py:class:`BaseBounds <taurus.entity.bounds.base_bounds.BaseBounds>`].

        """
        if 'conditions' in data and len(data['conditions']) != 0:
            data['conditions'] = [[ConditionTemplate.build(cond[0].as_dict()),
                                   loads(dumps(cond[1]))] for cond in data['conditions']]
        if 'parameters' in data and len(data['parameters']) != 0:
            data['parameters'] = [[ParameterTemplate.build(param[0].as_dict()),
                                   loads(dumps(param[1]))] for param in data['parameters']]

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
