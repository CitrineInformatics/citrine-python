"""Resources that represent process templates."""
from typing import List, Dict, Optional, Union, Sequence, Type

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, Mapping, Object, SpecifiedMixedList, \
    LinkOrElse
from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.data_concepts import DataConcepts
from citrine.resources.object_templates import ObjectTemplate, ObjectTemplateCollection
from citrine.resources.parameter_template import ParameterTemplate
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.template.process_template import ProcessTemplate as GEMDProcessTemplate


class ProcessTemplate(ObjectTemplate, Resource['ProcessTemplate'], GEMDProcessTemplate):
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
        `unique IDs <https://citrineinformatics.github.io/gemd-docs/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/gemd-docs/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    conditions: List[ConditionTemplate] or List[ConditionTemplate, \
    :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated conditions. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this condition.
    parameters: List[ParameterTemplate] or List[ParameterTemplate, \
    :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated parameters. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this parameter.

    """

    _response_key = GEMDProcessTemplate.typ  # 'process_template'

    name = String('name', override=True)
    description = PropertyOptional(String(), 'description', override=True)
    uids = Mapping(String('scope'), String('id'), 'uids', override=True)
    tags = PropertyOptional(PropertyList(String()), 'tags', override=True)
    conditions = PropertyOptional(PropertyList(SpecifiedMixedList(
        [LinkOrElse, PropertyOptional(Object(BaseBounds))])), 'conditions', override=True)
    parameters = PropertyOptional(PropertyList(SpecifiedMixedList(
        [LinkOrElse, PropertyOptional(Object(BaseBounds))])), 'parameters', override=True)
    allowed_labels = PropertyOptional(PropertyList(String()), 'allowed_labels', override=True)
    allowed_names = PropertyOptional(PropertyList(String()), 'allowed_names', override=True)
    typ = String('type')

    def __init__(self,
                 name: str,
                 *,
                 uids: Optional[Dict[str, str]] = None,
                 conditions: Optional[Sequence[Union[ConditionTemplate,
                                                     LinkByUID,
                                                     Sequence[Union[ConditionTemplate, LinkByUID,
                                                                    Optional[BaseBounds]]]
                                                     ]]] = None,
                 parameters: Optional[Sequence[Union[ParameterTemplate,
                                                     LinkByUID,
                                                     Sequence[Union[ParameterTemplate, LinkByUID,
                                                                    Optional[BaseBounds]]]
                                                     ]]] = None,
                 allowed_labels: Optional[List[str]] = None,
                 allowed_names: Optional[List[str]] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        if uids is None:
            uids = dict()
        DataConcepts.__init__(self, GEMDProcessTemplate.typ)
        GEMDProcessTemplate.__init__(self, name=name, uids=uids,
                                     conditions=conditions, parameters=parameters, tags=tags,
                                     description=description, allowed_labels=allowed_labels,
                                     allowed_names=allowed_names)

    def __str__(self):
        return '<Process template {!r}>'.format(self.name)


class ProcessTemplateCollection(ObjectTemplateCollection[ProcessTemplate]):
    """A collection of process templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/process-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/process-templates'
    _individual_key = 'process_template'
    _collection_key = 'process_templates'
    _resource = ProcessTemplate

    @classmethod
    def get_type(cls) -> Type[ProcessTemplate]:
        """Return the resource type in the collection."""
        return ProcessTemplate
