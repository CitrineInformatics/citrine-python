"""Resources that represent measurement templates."""
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
from citrine.resources.property_template import PropertyTemplate
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.template.measurement_template \
    import MeasurementTemplate as GEMDMeasurementTemplate


class MeasurementTemplate(ObjectTemplate,
                          Resource['MeasurementTemplate'], GEMDMeasurementTemplate):
    """
    A measurement template.

    Measurement templates are collections of condition, parameter and property templates that
    constrain the values of a measurement's condition, parameter and property attributes, and
    provide a common structure for describing similar measurements.

    Parameters
    ----------
    name: str
        The name of the measurement template.
    description: str, optional
        Long-form description of the measurement template.
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
    properties: List[PropertyTemplate] or List[PropertyTemplate, \
    :py:class:`BaseBounds <gemd.entity.bounds.base_bounds.BaseBounds>`], optional
        Templates for associated properties. Each template can be provided by itself, or as a list
        with the second entry being a separate, *more restrictive* Bounds object that defines
        the limits of the value for this property.

    """

    _response_key = GEMDMeasurementTemplate.typ  # 'measurement_template'

    name = String('name')
    description = PropertyOptional(String(), 'description')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    properties = PropertyOptional(PropertyList(
        SpecifiedMixedList([LinkOrElse, Object(BaseBounds)])), 'properties')
    conditions = PropertyOptional(PropertyList(
        SpecifiedMixedList([LinkOrElse, Object(BaseBounds)])), 'conditions')
    parameters = PropertyOptional(PropertyList(
        SpecifiedMixedList([LinkOrElse, Object(BaseBounds)])), 'parameters')
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
        if uids is None:
            uids = dict()
        DataConcepts.__init__(self, GEMDMeasurementTemplate.typ)
        GEMDMeasurementTemplate.__init__(self, name=name, properties=properties,
                                         conditions=conditions, parameters=parameters, tags=tags,
                                         uids=uids, description=description)

    def __str__(self):
        return '<Measurement template {!r}>'.format(self.name)


class MeasurementTemplateCollection(ObjectTemplateCollection[MeasurementTemplate]):
    """A collection of measurement templates."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/measurement-templates'
    _dataset_agnostic_path_template = 'projects/{project_id}/measurement-templates'
    _individual_key = 'measurement_template'
    _collection_key = 'measurement_templates'

    @classmethod
    def get_type(cls) -> Type[MeasurementTemplate]:
        """Return the resource type in the collection."""
        return MeasurementTemplate
